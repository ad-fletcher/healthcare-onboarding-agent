from livekit.agents import Agent, ChatContext, RunContext, get_job_context, function_tool
from livekit import api
import httpx
# Removed Dict import if only used by moved functions
# Removed dataclasses import as MySessionInfo is imported
# --- Import from new helper modules --- 
from helpers.shared_types import MySessionInfo, DEFAULT_PROGRESS # Import types/constants
from helpers.convex_utils import (
    update_demographic_field,
    contextual_analysis_tool,
    render_visualization,
    update_interview_progress,
    get_progress # Assuming get_progress was moved, add if so
)
from helpers.prompts import instructions_short
import logging # Add logging import

logger = logging.getLogger(__name__) # Add logger instance

class phase2Agent(Agent):
    def __init__(self, context: RunContext[MySessionInfo]): # Removed chat_ctx parameter
        # Ensure context and userdata are valid
        user_name = "there" # Default value
        profile = {} # Default value
        if context and context.session and hasattr(context.session, 'userdata') and isinstance(context.session.userdata, MySessionInfo):
            user_name = context.session.userdata.name or "there" 
            profile = context.session.userdata.profile or {}
        else:
            # Log a warning if context/userdata is not as expected
            logger.warning("AssistantLong initialized with invalid context or userdata.")
            
        # Pass relevant info to super()
        super().__init__(instructions=instructions_short) # Consider if INSTRUCTION needs context

    async def on_enter(self) -> None:
        user_name = "there"
        if self.session and hasattr(self.session, 'userdata') and isinstance(self.session.userdata, MySessionInfo):
             user_name = self.session.userdata.name or "there"
        else:
             logger.warning("on_enter: Could not retrieve user name from session userdata.")

        await self.session.say(f"Great, thank you {user_name}! Let's get started on building your health profile. This will be quick, is it okay if i pull up your information?")

    @function_tool()
    async def get_progress(self, context: RunContext[MySessionInfo]) -> dict:
        """
        Async query to Convex for which demographic fields are complete.
        Uses the imported get_progress function and DEFAULT_PROGRESS constant.
        Falls back to DEFAULT_PROGRESS on any error.
        """
        # Validate context and userdata before accessing
        if not context or not context.session or not hasattr(context.session, 'userdata') or not isinstance(context.session.userdata, MySessionInfo):
            logger.error("get_progress tool called with invalid context or userdata.")
            return DEFAULT_PROGRESS # Return default if context is invalid

        user_id = context.session.userdata.user_id
        if not user_id:
            logger.error("get_progress tool called but user_id is missing from session userdata.")
            return DEFAULT_PROGRESS # Return default if user_id missing

        # Use the imported get_progress function
        # Pass DEFAULT_PROGRESS as the fallback directly to the utility function
        progress_data = await get_progress(user_id, DEFAULT_PROGRESS)
        return progress_data
    

    @function_tool()
    async def record_visulization(self, field: str, user_value: str) -> dict:
        """
        Logs the user reponse and updates a visulization which will pop up on their screen.  You should log after eery answer you get

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
        # Validate session and userdata
        if not self.session or not hasattr(self.session, 'userdata') or not isinstance(self.session.userdata, MySessionInfo):
            logger.error("record_and_feedback tool called with invalid session or userdata.")
            return {'context of user Answer': "Error: Could not access required session information."}

        interview_id = self.session.userdata.interview_id
        user_id = self.session.userdata.user_id

        if not interview_id or not user_id:
            logger.error("record_and_feedback tool called but interview_id or user_id is missing.")
            return {'context of user Answer': "Error: Missing required identifiers."}

        # Use imported functions
        update_result = await update_demographic_field(user_id, field, user_value)
        if update_result.get("status") == "error":
            logger.warning(f"Failed to update demographic field '{field}' for user '{user_id}': {update_result.get('error_message')}")
            # Decide if you want to return an error or continue with feedback/viz
        
        # Call render_visualization but don't necessarily use its return value here unless needed
        viz_result = render_visualization(field, user_value, interview_id, user_id)
        if viz_result.get("logError"):
             logger.warning(f"Failed to log visualization for field '{field}': {viz_result['logError']}")

        # Return only the textual feedback as per original function signature
        return {'logging complete': 'success'}



    @function_tool()
    async def end_call(self, context: RunContext[MySessionInfo]) -> None:
        """Use this tool after you get answers to all the questions. Only use after you have collected answers to all the questions."""
        # Use the imported update_interview_progress function
        update_result = await update_interview_progress(context)
        if update_result.get("status") == "error":
            logger.error(f"Failed to update interview progress: {update_result.get('error_message')}")
            # Decide if we should still say goodbye or handle differently

        await self.session.say("Thank you for your time, this concludes the interview. Have a wonderful day.")
        
        job_ctx = get_job_context()
        if job_ctx and job_ctx.room and job_ctx.room.name:
            try:
                await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))
            except Exception as e:
                logger.error(f"Failed to delete room {job_ctx.room.name} after ending call: {e}")
        else:
            logger.warning("Could not delete room after ending call: Job context or room details missing.")

 