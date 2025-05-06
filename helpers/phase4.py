# phase4_agent.py  ― Option B (field tracked in code)
import asyncio, logging
from livekit.agents import Agent, RunContext, function_tool, get_job_context
from livekit import api

from helpers.shared_types import MySessionInfo
from helpers.convex_utils import (
    update_medical_profile_field,
    render_visualization,
    log_message_to_convex,
    update_interview_progress,
)
from helpers.prompts import PHASE4_INSTRUCTIONS

log = logging.getLogger(__name__)

# ───────────────────────── field meta ──────────────────────────
FIELD_INFO = {
    "currentMedications": {
        "prompt": "Are you currently taking any prescription or over‑the‑counter medications?",
        "literals": ["true", "false"],
        "followup": "Got it — could you list them briefly?"  # asked if true
    },
    "conditions": {
        "prompt": "Do you have any chronic medical conditions diagnosed by a professional?",
        "literals": ["true", "false"],
        "followup": "Could you mention which conditions?"   # asked if true
    },
    "surgeries": {
        "prompt": "Have you ever had surgery?",
        "literals": ["true", "false"],
        "followup": "What surgeries have you had?"          # asked if true
    },
    "emergencyVisits": {
        "prompt": "Have you visited an emergency department in the last five years?",
        "literals": ["true", "false"],
        "followup": "Could you share what happened and roughly when?"  # asked if true
    },
    "lastCheckup": {
        "prompt": (
            "When was your last routine check‑up: within a year, 1–2 years ago, "
            "more than 2 years ago, or never / not sure?"
        ),
        "literals": [
            "within_1_year",
            "1-2_years",
            "over_2_years",
            "never_unsure",
        ],
    },
    "familyHistory": {
        "prompt": (
            "Does anyone in your immediate family have significant hereditary "
            "conditions (like heart disease, cancer, diabetes)?"
        ),
        "literals": ["true", "false"],
    },
    "mentalHealth": {
        "prompt": (
            "How would you describe your mental health overall: generally good, "
            "consistently good, significant challenges, or prefer not to say?"
        ),
        "literals": [
            "generally_good",
            "consistently_good",
            "significant_challenges",
            "prefer_not_to_say",
        ],
    },
    "recordPermission": {
        "prompt": "Do I have your permission to store your health record securely for future care?",
        "literals": ["true", "false"],
    },
}
PHASE4_FIELDS = list(FIELD_INFO.keys())
PHASE_INDEX = 4
BOOL_FIELDS_WITH_FOLLOWUP = {
    k for k, v in FIELD_INFO.items() if v["literals"] == ["true", "false"] and "followup" in v
}
# ───────────────────────────────────────────────────────────────


class phase4Agent(Agent):
    """Medical‑profile interviewer."""

    def __init__(self, context: RunContext[MySessionInfo]):
        super().__init__(instructions=PHASE4_INSTRUCTIONS)
        self.context = context
        self.progress = (
            context.session.userdata.phase_progress.get(PHASE_INDEX, {})
            if context and context.session
            else {}
        )

    # ───────────── lifecycle ─────────────
    async def on_enter(self) -> None:
        name = self.session.userdata.name or "there"
        first_field = self._next_unanswered()
        if first_field:
            await self.session.say(
                f"Let’s finish with a quick medical profile, {name}. "
                f"{FIELD_INFO[first_field]['prompt']}"
            )
        else:
            await self.session.say(f"All medical‑profile items are already done, {name}!")

    # ───────────── helpers ──────────────
    def _next_unanswered(self) -> str | None:
        return next((k for k in PHASE4_FIELDS if not self.progress.get(k)), None)

    # ─────────── LLM tools ──────────────
    @function_tool()
    async def record_visualization(self, user_value: str) -> dict:
        field = self._next_unanswered()
        if field is None:
            await self.session.say("Everything’s captured—thank you!")
            return {"status": "already_complete", "next_field": None}

        allowed = FIELD_INFO[field]["literals"]
        if user_value not in allowed:
            await self.session.say(f"Please respond with: {', '.join(allowed)}.")
            return {"status": "retry_needed", "next_field": field}

        # 1. save
        try:
            await update_medical_profile_field(
                self.session.userdata.user_id, field, user_value
            )
            render_visualization(
                field,
                user_value,
                self.session.userdata.interview_id,
                self.session.userdata.user_id,
            )
        except Exception as e:
            log.error(f"Convex error for {field}: {e}", exc_info=True)
            await self.session.say("Hmm, I couldn’t save that—let’s try again.")
            return {"status": "error_saving", "next_field": field}

        # 2. mark progress
        self.progress[field] = True
        self.context.session.userdata.phase_progress.setdefault(PHASE_INDEX, {})[
            field
        ] = True

        # 3. optional follow‑up for boolean fields
        if field in BOOL_FIELDS_WITH_FOLLOWUP and user_value == "true":
            await self.session.say(FIELD_INFO[field]["followup"])

        next_field = self._next_unanswered()
        return {"status": "ok", "next_field": next_field}

    @function_tool()
    async def end_call(self) -> None:
        await self.session.say("All set! Thanks for completing your medical profile.")
        await log_message_to_convex(
            self.session.userdata.interview_id, "agent", "Phase 4 completed."
        )
        await update_interview_progress(self.context)

        job_ctx = get_job_context()
        if job_ctx and job_ctx.room:
            try:
                await job_ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=job_ctx.room.name)
                )
            except Exception as e:
                log.error(f"Room deletion failed: {e}")
