# phase3_agent.py  ― Option B (field tracked in code)
import asyncio, logging
from livekit.agents import Agent, RunContext, function_tool, get_job_context
from livekit import api

from helpers.shared_types import MySessionInfo
from helpers.convex_utils import (
    update_vitality_sign_field,
    render_visualization,
    log_message_to_convex,
    update_interview_progress,
)
from helpers.prompts import PHASE3_INSTRUCTIONS

log = logging.getLogger(__name__)

# ───────────────────────── field meta ──────────────────────────
FIELD_INFO = {
    "healthVision": {
        "prompt": (
            "When you picture ideal health, is it about mobility & independence, "
            "energy & vitality, prevention, a balanced mix, or something else?"
        ),
        "literals": [
            "mobility/independence focus",
            "energy/vitality focus",
            "prevention focus",
            "balanced focus",
            "other",
        ],
    },
    "moneyRelationship": {
        "prompt": (
            "Which best describes your money style — frugal, balanced, spendthrift, "
            "or other?"
        ),
        "literals": ["frugal", "balanced", "spendthrift", "other"],
    },
    "timeRelationship": {
        "prompt": (
            "Do you see time mostly as an investment, something neutral, a burden, "
            "or something else?"
        ),
        "literals": ["investment", "neutral", "burden", "other"],
    },
    "agingRelationship": {
        "prompt": (
            "How do you feel about aging — acceptance, avoidance, worry, or other?"
        ),
        "literals": ["acceptance", "avoidance", "worry", "other"],
    },
    "parentInfluence": {
        "prompt": (
            "How have your parents’ health journeys shaped you — learn from their "
            "mistakes, follow their example, neutral, complex, or other?"
        ),
        "literals": [
            "learn_from_mistakes",
            "follow_example",
            "neutral",
            "complex",
            "other",
        ],
    },
    "jobImpact": {
        "prompt": (
            "Does your job mostly add stress/inactivity, support well‑being, feel "
            "mixed, minimal, or other?"
        ),
        "literals": [
            "stress/inactivity",
            "well‑being_source",
            "mixed",
            "minimal",
            "other",
        ],
    },
    "foodRelationship": {
        "prompt": (
            "Is food primarily fuel, balanced nutrition, pleasure first, or other?"
        ),
        "literals": ["fuel_first", "balanced", "pleasure_first", "other"],
    },
    "techRelationship": {
        "prompt": (
            "Does technology feel like mainly a tool, a mixed blessing, mostly a "
            "distraction, or other?"
        ),
        "literals": ["mainly_tool", "mixed", "mostly_distraction", "other"],
    },
    "vanityRelationship": {
        "prompt": (
            "Is caring about appearance a primary focus, secondary, minimal, or other?"
        ),
        "literals": ["primary", "secondary", "minimal", "other"],
    },
    "mortalityPerspective": {
        "prompt": (
            "Do thoughts of mortality act as a motivator, an occasional thought, "
            "something you avoid, or other?"
        ),
        "literals": [
            "motivator",
            "occasional_thought",
            "avoidant",
            "other",
        ],
    },
}
PHASE3_FIELDS = list(FIELD_INFO.keys())
PHASE_INDEX = 3
# ───────────────────────────────────────────────────────────────


class phase3Agent(Agent):
    """Vitality‑signs interviewer."""

    def __init__(self, context: RunContext[MySessionInfo]):
        super().__init__(instructions=PHASE3_INSTRUCTIONS)
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
                f"Let’s explore your big‑picture goals, {name}. "
                f"{FIELD_INFO[first_field]['prompt']}"
            )
        else:
            await self.session.say(f"Looks like we covered vitality signs already, {name}!")

    # ───────────── helpers ──────────────
    def _next_unanswered(self) -> str | None:
        return next((k for k in PHASE3_FIELDS if not self.progress.get(k)), None)

    # ─────────── LLM tools ──────────────
    @function_tool()
    async def record_visualization(self, user_value: str) -> dict:
        field = self._next_unanswered()
        if field is None:
            await self.session.say("All set—thanks again!")
            return {"status": "already_complete", "next_field": None}

        allowed = FIELD_INFO[field]["literals"]
        if user_value not in allowed:
            await self.session.say(f"Please choose one of: {', '.join(allowed)}.")
            return {"status": "retry_needed", "next_field": field}

        try:
            await update_vitality_sign_field(
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
            await self.session.say("I couldn’t save that—let’s try again.")
            return {"status": "error_saving", "next_field": field}

        # Mark progress
        self.progress[field] = True
        self.context.session.userdata.phase_progress.setdefault(PHASE_INDEX, {})[
            field
        ] = True

        next_field = self._next_unanswered()
        return {"status": "ok", "next_field": next_field}

    @function_tool()
    async def end_call(self) -> None:
        await self.session.say("Wonderful! That wraps up your vitality‑signs section.")
        await log_message_to_convex(
            self.session.userdata.interview_id, "agent", "Phase 3 completed."
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
