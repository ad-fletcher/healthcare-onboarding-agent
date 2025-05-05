# helpers/shared_types.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os

# ---------------------------------------------------------------------------
# Convex endpoint
# ---------------------------------------------------------------------------
CONVEX_LOG_URL: str = os.getenv("CONVEX_LOG_URL", "")

# ---------------------------------------------------------------------------
# Default‑progress maps for each phase  (kept in one place)
# ---------------------------------------------------------------------------

DEFAULT_PROGRESS = {
    "age": False,
    "lifeStage": False,
    "livingArrangement": False,
    "location": False,
    "educationLevel": False,
    "careerField": False,
    "financialStability": False,
    "socialConnection": False,
    "healthConfidence": False,
    "lifeSatisfaction": False,
}
DEFAULT_PROGRESS_PHASE1 = {
    "age": False,
    "lifeStage": False,
    "livingArrangement": False,
    "location": False,
    "educationLevel": False,
    "careerField": False,
    "financialStability": False,
    "socialConnection": False,
    "healthConfidence": False,
    "lifeSatisfaction": False,
}

DEFAULT_PROGRESS_PHASE2 = {
    "safetyEquipmentUsage":   False,
    "treatmentPreference":    False,
    "headacheStrategy":       False,
    "newTreatmentOpenness":   False,
    "financialRisk":          False,
    "preventiveCareAttitude": False,
    "infoVerificationStyle":  False,
    "chestPainResponse":      False,
    "altMedicineOpenness":    False,
    "geneticTestingAttitude": False,
}

DEFAULT_PROGRESS_PHASE3 = {
    "healthVision":         False,
    "moneyRelationship":    False,
    "timeRelationship":     False,
    "agingRelationship":    False,
    "parentInfluence":      False,
    "jobImpact":            False,
    "foodRelationship":     False,
    "techRelationship":     False,
    "vanityRelationship":   False,
    "mortalityPerspective": False,
}

DEFAULT_PROGRESS_PHASE4 = {
    "currentMedications": False,
    "conditions":         False,
    "surgeries":          False,
    "emergencyVisits":    False,
    "lastCheckup":        False,
    "familyHistory":      False,
    "mentalHealth":       False,
    "recordPermission":   False,
}

# Convenience dict if you need to look them up dynamically
PHASE_DEFAULTS: Dict[int, Dict[str, bool]] = {
    1: DEFAULT_PROGRESS_PHASE1,
    2: DEFAULT_PROGRESS_PHASE2,
    3: DEFAULT_PROGRESS_PHASE3,
    4: DEFAULT_PROGRESS_PHASE4,
}

# ---------------------------------------------------------------------------
# Session‑scoped information the agent tree shares
# ---------------------------------------------------------------------------
@dataclass
class MySessionInfo:
    # IDs / identity
    clerk_id:     Optional[str] = None
    user_id:      Optional[str] = None
    name:         Optional[str] = None

    # Raw metadata blob if you want it
    profile:      Optional[Dict[str, Any]] = None

    # Current interview session
    interview_id: Optional[str] = None

    # --- NEW: multi‑phase progress bookkeeping -----------------------------
    # Full nested map {phase_int: {field: bool}}
    phase_progress: Dict[int, Dict[str, bool]] = field(default_factory=dict)

    # Earliest phase still incomplete (set by ConsentCollector)
    earliest_phase: Optional[int] = None
