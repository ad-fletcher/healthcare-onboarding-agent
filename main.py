# main.py
import os
import json
from dotenv import load_dotenv
import requests
from livekit import agents, rtc, api
from livekit.agents import AgentSession, Agent, RoomInputOptions, JobContext, function_tool, cli, get_job_context, ChatContext, RunContext, RoomOutputOptions
from livekit.plugins import openai, cartesia, deepgram, noise_cancellation, silero, elevenlabs
from livekit.plugins.turn_detector.multilingual import MultilingualModel
import time
import logging
# --- Add Imports ---
from livekit.agents import stt
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import unittest

# --- Import from new helper modules ---
from helpers.shared_types import MySessionInfo, CONVEX_LOG_URL, DEFAULT_PROGRESS
from helpers.convex_utils import (
    get_user_metadata,
    render_visualization, 
    contextual_analysis_tool, 
    log_message_to_convex,
    update_demographic_field, 
    update_interview_progress,
    get_progress # Assuming get_progress was moved, add if so
)



logger = logging.getLogger(__name__)

load_dotenv(dotenv_path='.env.local')


# --- Health Check Server --- <--- NEW
HEALTH_CHECK_PORT = 8082 # Port fly.toml will check. Changed from 8081.

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/healthz': # Standard health check path
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        # Optional: Silence the health check server logs
        return

def start_health_check_server(port):
    server_address = ('', port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    logger.info(f"Health check server listening on port {port}")
    httpd.serve_forever()
# --- End Health Check Server ---





class ConsentCollector(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
            
            Your are a voice AI agent with the singular task to see if the user wants have a quick interview or understand why these questions are being asked.

            Depending on their answer you will direct them to the appropriate interview, either long or short.
            
            After you ask what kind of interview they want, wait for a response from the user.

            If the user wants to know why the questions are being asked, you will direct them with the 'on_consent_givenLong' tool.
            If the user wants the quick interview, you will direct them with the 'on_consent_givenQuick' tool.



            """
        )
    async def on_enter(self) -> None:
        await self.session.say("Welcome to your health agent.  I'm Dr. Jordan. Our conversation will help create your health profile and identify preventive care opportunities, Would you like to have a quick interview or understand why these questions are being asked?")

    @function_tool()
    async def on_consent_givenLong(self, context: RunContext[MySessionInfo]):
        """Use this tool to indicate that consent has been given and the call may proceed."""
        # --- MOVED AssistantLong import here ---
        from helpers.assistantLong import AssistantLong 
        # ---------------------------------------
        
        clerk_id = self.session.userdata.clerk_id
        if not clerk_id:
            self.logger.error("Clerk ID not found in session userdata. Cannot fetch metadata.")
            return

        # Use the imported get_user_metadata function
        meta = get_user_metadata(clerk_id)
        if not meta or meta.get("status") == "error":
            self.logger.error(f"Failed to get user metadata for clerk_id {clerk_id}: {meta.get('error_message', 'Unknown error')}")
            return

        user_id = meta.get("user_id")
        name = meta.get("name")

        if not user_id or not name:
             self.session.logger.error(f"User ID or Name missing from metadata for clerk_id {clerk_id}: {meta}")
             return

        context.session.userdata.user_id = user_id
        context.session.userdata.name    = name
        context.session.userdata.profile = meta # Profile now contains the full metadata result
        
        # Instantiate AssistantLong without chat_ctx
        return AssistantLong(context=context)
    
    
    @function_tool()
    async def on_consent_givenQuick(self, context: RunContext[MySessionInfo]):
        """Use this tool to indicate that consent has been given and the call may proceed."""
        # --- MOVED AssistantLong import here ---
        from helpers.assistantQuick import AssistantQuick

        # ---------------------------------------
        
        clerk_id = self.session.userdata.clerk_id
        if not clerk_id:
            self.logger.error("Clerk ID not found in session userdata. Cannot fetch metadata.")
            return

        # Use the imported get_user_metadata function
        meta = get_user_metadata(clerk_id)
        if not meta or meta.get("status") == "error":
            self.logger.error(f"Failed to get user metadata for clerk_id {clerk_id}: {meta.get('error_message', 'Unknown error')}")
            return

        user_id = meta.get("user_id")
        name = meta.get("name")

        if not user_id or not name:
             self.session.logger.error(f"User ID or Name missing from metadata for clerk_id {clerk_id}: {meta}")
             return

        context.session.userdata.user_id = user_id
        context.session.userdata.name    = name
        context.session.userdata.profile = meta # Profile now contains the full metadata result
        
        # Instantiate AssistantLong without chat_ctx
        return AssistantQuick(context=context)
    
    @function_tool()
    async def end_call(self) -> None:
        """Use this tool to indicate that consent has not been given and the call should end."""
        await self.session.say("Thank you for your time, have a wonderful day.")
        job_ctx = get_job_context()

        if job_ctx and job_ctx.room and job_ctx.room.name:
            try:
                await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))
            except Exception as e:
                self.session.logger.error(f"Failed to delete room {job_ctx.room.name}: {e}")
        else:
            self.session.logger.warning("Could not delete room: Job context or room details missing.")








async def entrypoint(ctx: JobContext):
    # — 1) Connect & pull metadata —
    await ctx.connect()
    participant = await ctx.wait_for_participant()
    md = json.loads(participant.metadata or "{}")
    clerk_id     = md.get("clerk_id")
    interview_id = md.get("interviewId")
    if not (clerk_id and interview_id):
        raise RuntimeError("Missing clerk_id or interviewId in metadata")

    # +++ Instantiate TTS plugin first +++

    # +++++++++++++++++++++++++++++++++++

    # — 2) Build your AgentSession (plain Deepgram STT) —
    session = AgentSession[MySessionInfo](
        userdata=MySessionInfo(clerk_id=clerk_id, interview_id=interview_id),
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4.1"),
        tts=elevenlabs.TTS(
            voice_id="hld2bG9cSMuILFj7P5zm",
            model="eleven_flash_v2_5"
        ),
        vad=silero.VAD.load(),
        turn_detection='vad',
    )

    # — 3) Monkey‑patch session.say → logs agent replies —
    original_say = session.say
    async def say_and_log(text: str, **kwargs):
        await original_say(text, **kwargs)
        await log_message_to_convex(interview_id, "agent", text)
    session.say = say_and_log


    # — 5) Start the agent as usual —
    await session.start(
        room=ctx.room,
        agent=ConsentCollector(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
        room_output_options=RoomOutputOptions(
            transcription_enabled=True
        ),
    )


if __name__ == "__main__":
    # Start health check server in a background thread <--- NEW
    health_thread = threading.Thread(
        target=start_health_check_server,
        args=(HEALTH_CHECK_PORT,),
        daemon=True # Ensures thread exits when main program exits
    )
    health_thread.start()

    # Original startup code
    cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="health-agent",
            ws_url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
        )
    )