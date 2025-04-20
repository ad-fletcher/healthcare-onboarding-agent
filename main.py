# main.py
import os
import json
from dotenv import load_dotenv
from dataclasses import dataclass
import requests
from livekit import agents, rtc, api
from livekit.agents import AgentSession, Agent, RoomInputOptions, JobContext, function_tool, cli, get_job_context, ChatContext, RunContext, RoomOutputOptions
from livekit.plugins import openai, cartesia, deepgram, noise_cancellation, silero, elevenlabs
from livekit.plugins.turn_detector.multilingual import MultilingualModel
import time
from typing import Any, Union
from helpers.data import AGGREGATE_DATA, DEFAULT_PROGRESS
import httpx
from helpers.prompts import INSTRUCTION
import logging
# --- Add Imports ---
import httpx
import asyncio # <--- Import asyncio
from livekit.agents import stt
#from livekit import ChatEventType
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading



logger = logging.getLogger(__name__)

load_dotenv(dotenv_path='.env.local')


# --- Health Check Server --- <--- NEW
HEALTH_CHECK_PORT = 8081 # Port fly.toml will check

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


CONVEX_LOG_URL = os.getenv("CONVEX_LOG_URL", "https://kindred-mosquito-333.convex.site")

@dataclass
class MySessionInfo:
    clerk_id: str | None = None
    user_id: str  | None = None    # <-- new
    name:    str  | None = None    # <-- new
    profile: dict | None = None
    interview_id: str | None = None


def get_user_metadata(clerk_id: str) -> dict:
    url = f"{CONVEX_LOG_URL}/get-user-metadata"
    try:
        resp = requests.post(url, json={"clerk_id": clerk_id})
        if resp.status_code == 200:
            payload = resp.json().get("data", {})
            return {
                "user_id": payload.get("_id"),
                "name":    payload.get("fullName"),
                # keep the rest if you like:
                **{k: v for k, v in payload.items() 
                   if k not in ("_id", "fullName")}
            }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def render_visualization(field: str, user_value: Union[str, int, float], interview_id: str, user_id: str) -> dict:
    """
    Generate a bar chart visualization configuration based on aggregate data, then upload it to Convex.

    Args:
        field (str): The demographic or wellness field (e.g. "age", "financialStability").
        user_value (any): The user-provided value.
        interview_id (str): The session/ interview identifier.
        user_id (str): The user identifier (needed to log with convex).

    Returns:
        dict: Visualization configuration (and any log error if occurred).
    """
    # Check that the aggregate data exists for the field.
    if field not in AGGREGATE_DATA:
        return {
            "status": "error",
            "message": f"No aggregate data available for field '{field}'."
        }
    
    data_entry = AGGREGATE_DATA[field]
    bars = []
    chart_title = f"{field.capitalize()} Distribution"
    
    # Process numeric fields using distributions.
    if "distribution" in data_entry:
        distribution = data_entry["distribution"]
        try:
            numeric_value = float(user_value)
        except (ValueError, TypeError):
            numeric_value = None

        for bin_item in distribution:
            is_user = False
            start = bin_item.get("start")
            end   = bin_item.get("end")
            
            if numeric_value is not None:
                if end is None:
                    if numeric_value >= start:
                        is_user = True
                else:
                    if start <= numeric_value <= end:
                        is_user = True
            
            # Use the percentage value from the bin (accepts either "percentage" or "pct").
            pct_value = bin_item.get("percentage") or bin_item.get("pct")
            bars.append({
                "label": bin_item["label"],
                "value": pct_value,
                "isUserValue": is_user,
            })
    
    # Process enumerated fields using mapping.
    elif "mapping" in data_entry:
        mapping = data_entry["mapping"]
        for key, info in mapping.items():
            # A simple case-insensitive check.
            is_user = (str(user_value).lower() in key.lower())
            bars.append({
                "label": info["label"],
                "value": info["pct"],
                "isUserValue": is_user,
            })
    
    else:
        return {
            "status": "error",
            "message": f"Field '{field}' lacks distribution or mapping data."
        }
    
    # Map field names to more readable formats for chart titles
    field_name_mapping = {
        'age': 'Age',
        'lifeStage': 'Life Stage', 
        'livingArrangement': 'Living Arrangement',
        'location': 'Location',
        'educationLevel': 'Education Level',
        'careerField': 'Career Field',
        'financialStability': 'Financial Stability',
        'socialConnection': 'Social Connection', 
        'healthConfidence': 'Health Confidence',
        'lifeSatisfaction': 'Life Satisfaction'
    }
    
    # Update chart title with mapped name if available
    chart_title = f"{field_name_mapping.get(field, field.capitalize())} Distribution"

    
    # Package the visualization configuration.
    visualization = {
        "userId": user_id,
        "interviewId": interview_id,
        "question": field,
        "chartTitle": chart_title,
        "chartType": "bar",
        "bars": bars,
        "userValue": str(user_value),
        "timestamp": int(time.time() * 1000)
    }
    
    # Now POST this configuration to your Convex endpoint.
    try:
        # Make sure that CONVEX_LOG_URL is set to your Convex HTTP endpoint base URL.
        log_url = f"{CONVEX_LOG_URL}/log-visualization"
        response = requests.post(log_url, json=visualization)
        if response.status_code != 200:
            visualization["logError"] = f"Server responded with error: {response.text}"
    except Exception as e:
        visualization["logError"] = str(e)
    
    return visualization

def contextual_analysis_tool(field: str, user_value: Union[str, int, float]) -> str:
    """
    Return a short feedback sentence comparing the user's value or category
    to the community distribution or average, using data from AGGREGATE_DATA.
    """
    # If no data for this field, short-circuit.
    if field not in AGGREGATE_DATA:
        return f"Sorry, no contextual data is available for {field}."

    data_entry = AGGREGATE_DATA[field]

    # Handle numeric fields with distributions or averages
    if field in ["financialStability", "healthConfidence", "lifeSatisfaction"]:
        # Convert user_value to float if possible
        try:
            numeric_value = float(user_value)
        except ValueError:
            return f"I expected a numeric value for {field}, but got {user_value}."

        # 1) Check for an average
        avg = data_entry.get("average", None)
        # 2) Check for distribution
        dist = data_entry.get("distribution", [])

        # Build a short response comparing to average
        if avg is not None:
            if numeric_value < avg:
                response = f"Your {field} of {numeric_value:.1f} is below the community average of {avg:.1f}."
            elif numeric_value > avg:
                response = f"Your {field} of {numeric_value:.1f} is above the community average of {avg:.1f}."
            else:
                response = f"Your {field} is exactly the community average of {avg:.1f}."

        else:
            response = f"You reported {field} as {numeric_value}, but we have no average data to compare."

        # If a distribution is present, see which bin the user_value falls into
        if dist:
            # Find which bin user_value belongs to
            bin_label = None
            for b in dist:
                start = b["start"]
                end = b["end"]
                if end is None:  # e.g., 65+
                    if numeric_value >= start:
                        bin_label = b["label"]
                        break
                else:
                    if start <= numeric_value <= end:
                        bin_label = b["label"]
                        break
            if bin_label:
                # Find the matching bin to get the percentage
                match = next((x for x in dist if x["label"] == bin_label), None)
                if match:
                    bin_pct = match["pct"]
                    response += f" About {bin_pct}% of the community reports a {field} in the range {bin_label}."
        return response

    # Age distribution
    if field == "age":
        try:
            age_value = float(user_value)
        except ValueError:
            return f"I expected a numeric age, but got {user_value}."

        dist = data_entry.get("distribution", [])
        matching_label = None
        for bin_info in dist:
            start = bin_info["start"]
            end = bin_info["end"]
            if end is None:  # e.g. 65+
                if age_value >= start:
                    matching_label = bin_info["label"]
                    bin_pct = bin_info["percentage"]
                    break
            else:
                if start <= age_value <= end:
                    matching_label = bin_info["label"]
                    bin_pct = bin_info["percentage"]
                    break
        if matching_label:
            return (f"You're in the {matching_label} age range, which is about {bin_pct}% of our community.")
        else:
            return f"I couldn't find an age bin for {age_value}."

    # For enumerated fields with distribution
    if field in ["lifeStage", "livingArrangement", "location", "socialConnection"]:
        # user_value should be a string (the chosen enum).
        data_map = data_entry.get("mapping", {})
        # Some mappings may not be exact if user_value differs from CSV keys
        # e.g. "early career" => "Early Career"
        if user_value in data_map:
            label = data_map[user_value]["label"]
            pct   = data_map[user_value]["pct"]
            if label and pct > 0:
                return f"{pct}% of our community also reports '{label}'."
            elif label and pct == 0:
                return f"We currently don't have distribution data for '{label}'."
            else:
                return f"No known distribution data for {user_value}."
        else:
            return f"Sorry, I don't have a direct match for {user_value} in {field} distribution data."

    # Education Level
    if field == "educationLevel":
        data_map = data_entry.get("mapping", {})
        # The user might say "Bachelors Degree" or "Bachelors"
        # We'll do a simple best-match approach or direct key check.
        # For simplicity, check direct presence:
        if user_value in data_map:
            label = data_map[user_value]["label"]
            pct   = data_map[user_value]["pct"]
            return f"About {pct}% of the community has {label}."
        else:
            return f"I'm not sure how many of our community has '{user_value}' as their highest education."

    # Career Field
    if field == "careerField":
        data_map = data_entry.get("mapping", {})
        # Potential synonyms or direct matches
        for k, v in data_map.items():
            # e.g. user_value = "Tech" -> we want to match "Technology"
            if user_value.lower() in k.lower():
                return f"About {v['pct']}% of our community works in {v['label']}."
        # If no match found
        return f"I don't have distribution data for the career field '{user_value}'."

    # If we get here, we didn't handle something
    return f"Sorry, no contextual feedback available for {field}."
 
async def log_message_to_convex(interview_id: str | None, author: str, text: str):
    if not interview_id:
        logger.warning("Cannot log message to Convex: interview_id is missing.")
        return
    if not CONVEX_LOG_URL or "YOUR_CONVEX_URL" in CONVEX_LOG_URL:
        logger.error("Cannot log message to Convex: CONVEX_LOG_URL not set.")
        return

    # Convex HTTP functions live under /api/<fnName>
    endpoint_path = "/addMessage"
    url = f"{CONVEX_LOG_URL}{endpoint_path}"

    payload = {
        "interviewId": interview_id,
        "author":      author,
        "text":        text,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            logger.info(f"Logged to Convex: {author=} {interview_id=} status={resp.status_code}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} from {url}: {await e.response.aread()}")
    except Exception as e:
        logger.error(f"Error logging to Convex ({url}): {e}")

async def update_demographic_field(user_id: str,field: str,value: str) -> dict:
    """
    Async version: updates a user's demographic field in Convex.
    """
    url = f"{CONVEX_LOG_URL}/update-demographic"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                url,
                json={
                    "user_id": user_id,
                    "field":   field,
                    "value":   value
                },
                timeout=5.0
            )
            resp.raise_for_status()
            return {"status": "success", "message": f"{field} updated"}

        except httpx.RequestError as e:
            logger.warning(f"update_demographic_field network error: {e}")
            return {"status": "error", "error_message": str(e)}

        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            text = await e.response.aread()
            logger.warning(f"update_demographic_field HTTP {code}: {text}")
            return {"status": "error", "error_message": text}


async def update_interview_progress(self, context: RunContext) -> dict:
    """
    Tells our Convex HTTP route to set interviewProgress = 1 for this user.
    """
    clerk_id = context.session.userdata.clerk_id
    url = f"{CONVEX_LOG_URL}/update-interview-progress"
    payload  = {"clerkId": clerk_id, "newProgress": 1}

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, timeout=5.0)
        resp.raise_for_status()
        return resp.json()




class ConsentCollector(Agent):
    def __init__(self):
        super().__init__(
            instructions="""Your are a voice AI agent with the singular task to collect positive consent from the user. If consent is not given, you must end the call.
            If the user asks questions about if their data is protected, you must answer that they get to decide how their data is used adn that it is protected.

            After you first ask, wait for a response from the user.
            """
        )
    async def on_enter(self) -> None:
        await self.session.say("Welcome to your health agent. I'm Dr. Jordan. Our conversation will help create your health profile and identify preventive care opportunities. Is that okay with you?")

    @function_tool()
    async def on_consent_given(self, context: RunContext[MySessionInfo]):
        """Use this tool to indicate that consent has been given and the call may proceed."""
        # Perform a handoff, immediately transfering control to the new agent
        clerk_id = self.session.userdata.clerk_id
        if not clerk_id:
            self.logger.error("Clerk ID not found in session userdata. Cannot fetch metadata.")
            # Decide how to handle this - maybe end the call or proceed without user info?
            # For now, let's just prevent the handoff:
            return

        meta = get_user_metadata(clerk_id)
        if not meta or meta.get("status") == "error":
            self.logger.error(f"Failed to get user metadata for clerk_id {clerk_id}: {meta}")
            # Again, decide how to handle - for now, prevent handoff
            return

        # Proceed only if clerk_id exists and meta is valid
        user_id = meta.get("user_id")
        name = meta.get("name")

        if not user_id or not name:
             self.session.logger.error(f"User ID or Name missing from metadata for clerk_id {clerk_id}: {meta}")
             # Handle missing specific fields if necessary
             return

        context.session.userdata.user_id = user_id
        context.session.userdata.name    = name
        context.session.userdata.profile = meta
        return Assistant(chat_ctx=self.chat_ctx, context=context)
    
    @function_tool()
    async def end_call(self) -> None:
        """Use this tool to indicate that consent has not been given and the call should end."""
        await self.session.say("Thank you for your time, have a wonderful day.")
        job_ctx = get_job_context()

        # Add checks for job_ctx and room details
        if job_ctx and job_ctx.room and job_ctx.room.name:
            try:
                await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))
            except Exception as e:
                # Log the error if deletion fails
                self.session.logger.error(f"Failed to delete room {job_ctx.room.name}: {e}")
        else:
            self.session.logger.warning("Could not delete room: Job context or room details missing.")





class Assistant(Agent):
    def __init__(self, chat_ctx: ChatContext, context: RunContext[MySessionInfo]):
        user_name = context.session.userdata.name or "there" # Default to 'there' if name is None
        profile = context.session.userdata.profile or {} # Default to an empty dict if profile is None

        super().__init__(instructions=INSTRUCTION)
    async def on_enter(self) -> None:
        # pull the name (or default to "there")
        user_name = self.session.userdata.name or "there"
        # send a personalized greeting
        profile = self.session.userdata.profile or {} # Default to an empty dict if profile is None

        await self.session.say(f"Great, thank you {user_name}! Let's get started on building your health profile. Let me pull up if we have any information about you. Is that okay?")

    @function_tool()
    async def get_progress(self, context: RunContext[MySessionInfo]) -> dict:
        """
        Async query to Convex for which demographic fields are complete.
        Falls back to DEFAULT_PROGRESS on any error.
        """
        user_id = context.session.userdata.user_id
        url     = f"{CONVEX_LOG_URL}/get-progress"

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json={"user_id": user_id}, timeout=5.0)
                resp.raise_for_status()
                data = resp.json()
                # ensure we only return the expected keys
                return {**DEFAULT_PROGRESS, **{k: bool(data.get(k, False)) for k in DEFAULT_PROGRESS}}

            except httpx.RequestError as e:
                self.logger.warning(f"get_progress network error: {e}")
            except httpx.HTTPStatusError as e:
                self.logger.warning(f"get_progress bad status ({e.response.status_code}): {e.response.text}")
            except ValueError as e:
                self.logger.warning(f"get_progress invalid JSON: {e}")

        # on any failure, return the default map
        return DEFAULT_PROGRESS
    

    @function_tool()
    async def record_and_feedback(self, field: str, user_value: str) -> dict:
        """
        Combines textual feedback with visualization and logs the user's response.

        Args:
            field (str): One of:
                - Numeric fields (as strings): 'age', 'financialStability', 'healthConfidence', 'lifeSatisfaction'
                - Categorical fields:
                    * lifeStage: 'education/training','early career','established career',
                                'family formation','empty nest','retirement preparation'
                    * livingArrangement: 'alone','roommates','partner','family','other'
                    * location: 'urban','suburban','rural'
                    * socialConnection: 'very strong','adequate','limited'
                    # educationLevel: ' 'High School','Some College','Bachelors','Graduate'
                    * careerField: 'Technology','Healthcare','Education','Business/Finance','Other'
            user_value (str):
                - For numeric fields: a numeric string (e.g. '29', '7')
                - For categorical fields: **exactly** one of the allowed options above

        Returns:
            dict: Contains:
                - 'textualFeedback': personalized feedback string
                and logs a visualization based on AGGREGATE_DATA[field].
        """

        interview_id = self.session.userdata.interview_id
        user_id = self.session.userdata.user_id
        await update_demographic_field(user_id, field, user_value)
        text_feedback = contextual_analysis_tool(field, user_value)
        viz_result = render_visualization(field, user_value, interview_id, user_id)
        return {'context of user Answer': text_feedback}

    @function_tool()
    async def end_call(self, context: RunContext[MySessionInfo]) -> None:
        """Use this tool after you get answers to all the questions.  Only use after you have collected answers to all the questions."""
        await self.session.say("Thank you for your time, this concludes the interview. Have a wonderful day.")
        job_ctx = get_job_context()
        await update_interview_progress(self, context)

        # Add checks for job_ctx and room details
        if job_ctx and job_ctx.room and job_ctx.room.name:
            try:
                await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))


            except Exception as e:
                # Log the error if deletion fails
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



    # — 2) Build your AgentSession (plain Deepgram STT) —
    session = AgentSession[MySessionInfo](
        userdata=MySessionInfo(clerk_id=clerk_id, interview_id=interview_id),
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4.1"),
        tts=lambda: elevenlabs.TTS(  # Defer initialization until needed
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