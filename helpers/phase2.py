# phase2_agent.py  ― Option B (field tracked in code)
import asyncio, logging
from livekit.agents import Agent, RunContext, function_tool, get_job_context
from livekit import api

from helpers.shared_types import MySessionInfo
from helpers.convex_utils import (
    update_risk_tolerance_field,      # ← implement in helpers if not present
    render_visualization,
    contextual_analysis_tool,
    log_message_to_convex,
    update_interview_progress,
)
from helpers.prompts import PHASE2_INSTRUCTIONS

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
FIELD_INFO = {
    "safetyEquipmentUsage": {
        "prompt": (
            "How often do you use safety gear like seat belts or bike helmets — "
            "always, sometimes, rarely, or never?"
        ),
        "literals": ["always", "sometimes", "rarely", "never"],
    },
    "treatmentPreference": {
        "prompt": (
            "If you injured your knee, would you lean toward physical therapy, an injection, "
            "surgery, or managing it yourself?"
        ),
        "literals": [
            "physical_therapy",
            "injection",
            "surgery",
            "self_manage",
        ],
    },
    "headacheStrategy": {
        "prompt": (
            "When a headache starts, do you take medication right away, wait and see, "
            "or try non‑medication options first?"
        ),
        "literals": [
            "medication_immediately",
            "wait_and_see",
            "non_medication_first",
        ],
    },
    "newTreatmentOpenness": {
        "prompt": (
            "When a new treatment comes out, do you try it immediately, wait until it’s "
            "well‑established, or stick with traditional care?"
        ),
        "literals": [
            "try_immediately",
            "wait_until_established",
            "stick_with_traditional",
        ],
    },
    "financialRisk": {
        "prompt": (
            "Would you pay out‑of‑pocket for a promising but unproven therapy — willing, "
            "maybe, or unwilling?"
        ),
        "literals": ["willing", "maybe", "unwilling"],
    },
    "preventiveCareAttitude": {
        "prompt": (
            "Do you schedule preventive check‑ups on time, only when convenient, "
            "or only if symptoms arise?"
        ),
        "literals": [
            "on_schedule",
            "when_convenient",
            "only_when_symptoms",
        ],
    },
    "infoVerificationStyle": {
        "prompt": (
            "When you hear a health tip online, do you adopt it, research it yourself, "
            "or ask a provider first?"
        ),
        "literals": [
            "adopt_immediately",
            "research_first",
            "ask_provider",
        ],
    },
    "chestPainResponse": {
        "prompt": (
            "If you felt sudden chest pain, would you call 911, book an urgent appointment, "
            "or wait it out?"
        ),
        "literals": [
            "call_ems",
            "urgent_appointment",
            "wait_and_see",
        ],
    },
    "altMedicineOpenness": {
        "prompt": (
            "How open are you to alternative medicine — eager, somewhat open, or not open?"
        ),
        "literals": ["eager", "somewhat_open", "not_open"],
    },
    "geneticTestingAttitude": {
        "prompt": (
            "How do you feel about genetic testing for health risks — eager to know, "
            "cautiously interested, or prefer not to know?"
        ),
        "literals": [
            "eager_to_know",
            "cautiously_interested",
            "prefer_not_to_know",
        ],
    },
}
PHASE2_FIELDS = list(FIELD_INFO.keys())  # keeps original order
PHASE_INDEX = 2
# ---------------------------------------------------------------------------


class phase2Agent(Agent):
    """Risk‑tolerance interviewer (field key tracked internally)."""

    def __init__(self, context: RunContext[MySessionInfo]):
        super().__init__(instructions=PHASE2_INSTRUCTIONS)
        self.context = context
        # Progress map for Phase 2
        self.progress = (
            context.session.userdata.phase_progress.get(PHASE_INDEX, {})
            if context and context.session
            else {}
        )

    # ───────────────────────── lifecycle ─────────────────────────

    async def on_enter(self) -> None:
        name = self.session.userdata.name or "there"
        first_field = self._determine_current_field()

        if first_field:
            log.info(f"Phase 2 starting/resuming. First required field: {first_field}")
            await self.session.say(
                f"Thanks for sticking with me, {name}! "
                f"{FIELD_INFO[first_field]['prompt']}"
            )
        else:
            log.info("Phase 2 entered, but all fields already complete.")
            await self.session.say(
                f"Welcome back, {name}! It looks like we’ve already covered this Phase."
            )
            # You could invoke end_call() automatically here if desired.
            

    # ───────────────────────── helpers ──────────────────────────

    def _determine_current_field(self) -> str | None:
        """Return the first field that has not yet been completed, or None if all done."""
        for key in PHASE2_FIELDS:
            if not self.progress.get(key):
                return key
        return None

    # ──────────────────────── LLM tools ─────────────────────────

    @function_tool()
    async def record_visualization(self, user_value: str) -> dict:
        field = self._determine_current_field()
        log.debug(f"record_visualization called. Current field: {field}")

        if field is None:
            await self.session.say("Looks like we’re all set—thanks!")
            return {"status": "already_complete", "next_field": None}

        info = FIELD_INFO[field]
        if user_value not in info["literals"]:
            log.warning(
                f"Validation failed for field '{field}'. "
                f"Value '{user_value}' not in allowed {info['literals']}"
            )
            await self.session.say(
                f"Sorry, I need one of these options: {', '.join(info['literals'])}."
            )
            return {"status": "retry_needed", "next_field": field}

        # 1. save to Convex
        try:
            await update_risk_tolerance_field(
                self.session.userdata.user_id, field, user_value
            )
            render_visualization(
                field, user_value, self.session.userdata.interview_id, self.session.userdata.user_id
            )
        except Exception as e:
            log.error(f"Convex update/render error for {field}: {e}", exc_info=True)
            await self.session.say("Hmm, I couldn’t save that—let’s try again.")
            return {"status": "error_saving", "next_field": field}

        # 2. mark progress locally & persist to session
        self.progress[field] = True
        if self.context and self.context.session:
            self.context.session.userdata.phase_progress.setdefault(PHASE_INDEX, {})[
                field
            ] = True

        next_field = self._determine_current_field()
        log.info(f"record_visualization ok → next_field={next_field}")
        return {"status": "ok", "next_field": next_field}

    @function_tool()
    async def end_call(self) -> None:
        """Runs when all 10 risk‑tolerance questions are answered."""
        await self.session.say(
            "Great! That wraps up the risk‑tolerance section. Thanks for sharing."
        )
        await log_message_to_convex(
            self.session.userdata.interview_id, "agent", "Phase 2 completed."
        )

        # mark interviewProgress = 2
        await update_interview_progress(self.context)

        # Close LiveKit room
        job_ctx = get_job_context()
        if job_ctx and job_ctx.room:
            try:
                await job_ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=job_ctx.room.name)
                )
            except Exception as e:
                log.error(f"Failed to delete room {job_ctx.room.name}: {e}")
