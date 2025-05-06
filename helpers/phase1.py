# phase1_agent.py  ― Option B (field tracked in code)

import asyncio, logging
from livekit.agents import Agent, RunContext, function_tool, get_job_context
from livekit import api

from helpers.shared_types import MySessionInfo
from helpers.convex_utils import (
    update_demographic_field,
    render_visualization,
    log_message_to_convex,
    update_interview_progress,
)
from helpers.prompts import PHASE1_INSTRUCTIONS

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
FIELD_INFO = {
    "age": {
        "prompt": "How young do you feel — what's your age in years?",
        "expected": "INTEGER between 18 and 120",
        # numeric → keep raw, bin later if you want
    },
    "lifeStage": {
        "prompt": (
            "Which life stage best describes you? "
            "(education/training, early career, established career, "
            "family formation, empty nest, retirement preparation)"
        ),
        "literals": [
            "education/training",
            "early career",
            "established career",
            "family formation",
            "empty nest",
            "retirement preparation",
        ],
    },
    "livingArrangement": {
        "prompt": (
            "What's your living situation: alone, roommates, partner, family, or other?"
        ),
        "literals": ["alone", "roommates", "partner", "family", "other"],
    },
    "location": {
        "prompt": "Would you say your home is urban, suburban, or rural?",
        "literals": ["urban", "suburban", "rural"],
    },
    "educationLevel": {
        "prompt": (
            "What's the highest education level you've completed "
            "(High School, Some College, Bachelors, Graduate)?"
        ),
        "literals": ["High School", "Some College", "Bachelors", "Graduate"],
    },
    "careerField": {
        "prompt": (
            "What general field do you work in (Technology, Healthcare, Education, "
            "Business/Finance, Other)?"
        ),
        "literals": [
            "Technology",
            "Healthcare",
            "Education",
            "Business/Finance",
            "Other",
        ],
    },
    "financialStability": {
        "prompt": (
            "On a scale of 1 (Searching) to 10 (Thriving), how would you rate your "
            "financial stability?"
        ),
        "expected": "INTEGER 1‑10",
    },
    "socialConnection": {
        "prompt": (
            "How would you describe your social support network — very strong, adequate, "
            "or limited?"
        ),
        "literals": ["very strong", "adequate", "limited"],
    },
    "healthConfidence": {
        "prompt": (
            "On a scale of 1 (Lost) to 10 (Expert Navigator), how confident are you "
            "navigating healthcare?"
        ),
        "expected": "INTEGER 1‑10",
    },
    "lifeSatisfaction": {
        "prompt": (
            "On a scale of 1 (Pretty Rough) to 10 (Loving It), how satisfied are you "
            "with life overall?"
        ),
        "expected": "INTEGER 1‑10",
    },
}
PHASE1_FIELDS = list(FIELD_INFO.keys())  # keeps original order
# ---------------------------------------------------------------------------



class phase1Agent(Agent):
    """Demographic‑intake interviewer (field key tracked internally)."""

    def __init__(self, context: RunContext[MySessionInfo]):
        super().__init__(instructions=PHASE1_INSTRUCTIONS,
                         )
        self.context = context
        # Progress map indicating which fields have been completed.
        self.progress = (
            context.session.userdata.phase_progress.get(1, {})
            if context and context.session else {}
        )

        # No cursor/current_field needed; the LLM drives the flow.

    # ───────────────────────── lifecycle ─────────────────────────

    async def on_enter(self) -> None:
        name = self.session.userdata.name or "there"
        first_field = self._determine_current_field()

        if first_field:
            # Handles both starting from scratch and resuming a partially completed phase.
            log.info(f"Phase 1 starting or resuming. First required field: {first_field}")
            first_prompt = FIELD_INFO[first_field]["prompt"]
            # Combine greeting with the first specific unanswered question
            await self.session.say(
                f"Great, thank you {name}! Let's dive in. "
                f"{first_prompt}"
            )
        else:
            # Only runs if ALL phase 1 fields were already marked as complete upon entry.
            log.info("Phase 1 entered, but all fields for this phase are already complete.")
            await self.session.say(
                f"Welcome back, {name}! It looks like we've already covered all the background questions for this section."
            )
            # Consider calling end_call or triggering next phase if appropriate
            # await self.end_call() # Or potentially signal completion differently

    # ───────────────────────── helpers ──────────────────────────

    def _determine_current_field(self) -> str | None:
        """Return the first field that has not yet been completed, or None if all done."""
        for key in PHASE1_FIELDS:
            if not self.progress.get(key):
                return key
        return None

    # ──────────────────────── LLM tools ─────────────────────────

    # ───── new record_visualization method (copy‑paste) ──────
    @function_tool()
    async def record_visualization(self, user_value: str) -> dict:
        # Determine which field is currently being answered based on progress.
        field = self._determine_current_field()
        log.debug(f"record_visualization called. Determined current field: {field}")

        if field is None:
            # All fields seem complete; allow the LLM flow to handle calling end_call.
            await self.session.say("It looks like we've already covered everything—thanks!")
            log.info("record_visualization: All fields already complete.")
            return {"status": "already_complete", "next_field": None}

        sd = self.session.userdata
        info = FIELD_INFO[field]
        log.debug(f"Processing field '{field}' with value '{user_value}'. Expected: {info.get('expected', info.get('literals'))}")

        # 1. verify the LLM obeyed the contract -----------
        if "literals" in info:
            allowed = info["literals"]
            if user_value not in allowed:
                log.warning(f"Validation failed for field '{field}'. Value '{user_value}' not in allowed: {allowed}")
                await self.session.say(
                    f"Sorry, I need one of the listed options: {', '.join(allowed)}."
                )
                # Return current field so LLM retries the same question
                return {"status": "retry_needed", "next_field": field}

        elif "expected" in info:
            try:
                num = int(user_value)
                # Combined validation logic
                valid = False
                if field == "age":
                    valid = 18 <= num <= 120
                    msg = "Could you confirm your age (between 18 and 120)?"
                elif field in {"financialStability", "healthConfidence", "lifeSatisfaction"}:
                    valid = 1 <= num <= 10
                    msg = "Please choose a number between 1 and 10."
                else:
                    valid = True # Should not happen based on FIELD_INFO, but safest

                if not valid:
                    log.warning(f"Validation failed for numeric field '{field}'. Value '{num}' out of range.")
                    await self.session.say(msg)
                    return {"status": "retry_needed", "next_field": field}

            except ValueError:
                log.warning(f"Validation failed for numeric field '{field}'. Value '{user_value}' is not an integer.")
                await self.session.say("Could you give me just the number?")
                # Return current field so LLM retries the same question
                return {"status": "retry_needed", "next_field": field}

        # 2. write straight to Convex ---------------------
        try:
            log.debug(f"Attempting Convex update for field: {field}, value: {user_value}")
            await update_demographic_field(sd.user_id, field, user_value)
            log.debug(f"Successfully updated demographic field: {field}")
            render_visualization(field, user_value, sd.interview_id, sd.user_id)
            log.debug(f"Successfully rendered visualization for field: {field}")
        except Exception as e:
            log.error(f"Error during Convex update/render for field {field}: {e}", exc_info=True)
            # Decide how to handle error - return current field to retry?
            await self.session.say("Sorry, there was an issue saving that. Let's try again.")
            return {"status": "error_saving", "next_field": field}

        # 3. mark progress so the next call works off the updated state
        self.progress[field] = True
        log.debug(f"Updated internal progress for field: {field}. Current progress: {self.progress}")
        # Persist progress back onto the shared session info so that other components see it.
        try:
            if self.context and self.context.session and hasattr(self.context.session, "userdata"):
                if 1 not in self.context.session.userdata.phase_progress:
                    self.context.session.userdata.phase_progress[1] = {}
                self.context.session.userdata.phase_progress[1][field] = True
                log.debug(f"Persisted progress to session userdata for field: {field}")
        except Exception as e:
            # Use warning, not error, as it's bookkeeping
            log.warning(f"Failed to persist progress to session userdata for field {field}: {e}")
            pass  # Don't let a bookkeeping failure break the flow

        # 4. Determine the next field to guide the LLM
        next_field = self._determine_current_field()
        log.debug(f"Determined next field: {next_field}")

        # Return status and the key for the next question (or None if done)
        log.info(f"Returning from record_visualization: status=ok, next_field={next_field}")
        return {"status": "ok", "next_field": next_field}

    @function_tool()
    async def end_call(self) -> None:
        """Runs automatically when all 10 questions are answered."""
        await self.session.say(
            "Thanks! That completes the background section. We'll move on shortly."
        )
        await log_message_to_convex(
            self.session.userdata.interview_id, "agent", "Phase 1 completed."
        )

        # mark interviewProgress = 1
        await update_interview_progress(self.context, 1)

        # hand control back to orchestrator or close room
        job_ctx = get_job_context()
        if job_ctx and job_ctx.room:
            try:
                await job_ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=job_ctx.room.name)
                )
            except Exception as e:
                log.error(f"Failed to delete room {job_ctx.room.name}: {e}")
