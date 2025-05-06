# main.py
import os
import json
from dotenv import load_dotenv
import requests
from livekit import agents, rtc, api
from livekit.agents import AgentSession, Agent, RoomInputOptions, JobContext, function_tool, cli, get_job_context, RunContext, RoomOutputOptions
from livekit.plugins import openai, cartesia, deepgram, noise_cancellation, silero, elevenlabs
from livekit.plugins.turn_detector.multilingual import MultilingualModel
import time
import logging
# --- Add Imports ---
from livekit.agents import stt
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import unittest

# Load environment variables from .env.local FIRST
load_dotenv(dotenv_path='.env.local')

# --- Import from new helper modules ---
# Now these imports will see the loaded environment variables
from helpers.shared_types import MySessionInfo
from helpers.convex_utils import (
    get_user_metadata,
    render_visualization, 
    contextual_analysis_tool, 
    log_message_to_convex,
    update_demographic_field, 
    update_interview_progress,
    get_progress, # Assuming get_progress was moved, add if so
    get_phase_progress
)



logger = logging.getLogger(__name__)

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



# consent_collector.py
from livekit.agents import Agent, RunContext, function_tool, get_job_context
from livekit import api
from helpers.shared_types import MySessionInfo

from helpers.convex_utils import (
    get_user_metadata,
    get_phase_progress,
)

from helpers.phase1 import phase1Agent
from helpers.phase2 import phase2Agent
from helpers.phase3 import phase3Agent
from helpers.phase4 import phase4Agent


class ConsentCollector(Agent):
    """
    Greeter + router.  It:
    1. Looks up user’s phase progress.
    2. Greets and asks for readiness.
    3. On 'yes', automatically instantiates the correct phase agent (1‑4).
       On 'no', ends the call.
    """

    def __init__(self, context):
        self._boot_ran = False
        super().__init__(
            instructions="""
            You are Dr Jordan, a warm AI assistant. 
            First greet the user and ask if they are ready to continue their
            health interview.  Do **not** ask any other questions.

            *If the user indicates they are ready*, call the internal
            `route_to_phase()` tool **exactly once**.  The tool already knows
            which phase is next, you do not need to pass arguments.

            *If the user says they are not ready*, politely acknowledge and
            call `end_call()`.

            Never mention tools, phases, code, or JSON aloud.
            """,
        )
        self.context = context
        self.earliest_phase: int | None = None

    # ───────────────────────── bootstrap ─────────────────────────

    async def _bootstrap_user(self):
        """Fetch metadata & progress once per session."""
        if self._boot_ran:
            return

        clerk_id = self.session.userdata.clerk_id
        meta = get_user_metadata(clerk_id)  # sync helper
        user_id = meta.get("user_id")

        earliest, all_maps = await get_phase_progress(user_id)

        info = self.session.userdata
        info.user_id        = user_id
        info.name           = meta.get("name")
        info.phase_progress = all_maps
        info.earliest_phase = earliest

        self.earliest_phase = earliest
        self._boot_ran = True
        logger.info(f"Bootstrap complete → earliest_phase={earliest}")

    # ───────────────────────── lifecycle ─────────────────────────

    async def on_enter(self) -> None:
        await self._bootstrap_user()
        await self.session.say(
            "Welcome! I’m Dr. Jordan. I’ll guide you through your health profile. "
            "Are you ready to get started?"
        )

    # ───────────────────────── routing tool ──────────────────────

    @function_tool()
    async def route_to_phase(self, context: RunContext[MySessionInfo]):
        """
        Internal tool – no args. Instantiates the appropriate phase agent
        based on self.earliest_phase and transfers control.
        """
        phase_map = {
            1: phase1Agent,
            2: phase2Agent,
            3: phase3Agent,
            4: phase4Agent,
        }

        # Default when everything is complete
        if not self.earliest_phase:
            await self.session.say(
                "Fantastic, all sections are already complete. Nothing more to do!"
            )
            await self.end_call()
            return  # nothing to return

        agent_cls = phase_map.get(self.earliest_phase)
        if not agent_cls:
            await self.session.say(
                "Hmm, I’m not sure which section is next. Let’s try again later."
            )
            await self.end_call()
            return

        # Instantiate and return the next phase agent.
        logger.info(f"Routing to Phase {self.earliest_phase} agent.")
        return agent_cls(context=context)

    # ───────────────────────── end‑call tool ─────────────────────

    @function_tool()
    async def end_call(self) -> None:
        """Politely end the session and close the LiveKit room."""
        await self.session.say("Thank you for your time. Have a wonderful day!")
        job_ctx = get_job_context()
        if job_ctx and job_ctx.room:
            try:
                await job_ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=job_ctx.room.name)
                )
            except Exception as e:
                logger.error(f"Failed to delete room {job_ctx.room.name}: {e}")





async def entrypoint(ctx: JobContext):
    # — 1) Connect & pull metadata —
    await ctx.connect()
    participant = await ctx.wait_for_participant()


    #interview_id = 'jd72nebkebcnae12qj0jf8ea0s7eaebn'
    #clerk_id = 'user_2wgVfwktDjgikGID2kJNDi0IqnO'


    ### NEEED THESE
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
        #tts=elevenlabs.TTS(
        #    voice_id="hld2bG9cSMuILFj7P5zm",
        #    model="eleven_flash_v2_5"),
        tts=cartesia.TTS(),

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
        agent=ConsentCollector(context=ctx),
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