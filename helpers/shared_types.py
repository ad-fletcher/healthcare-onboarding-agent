from dataclasses import dataclass
import os

# Define CONVEX_LOG_URL using os.getenv as it was originally
CONVEX_LOG_URL = os.getenv("CONVEX_LOG_URL", "")

@dataclass
class MySessionInfo:
    clerk_id: str | None = None
    user_id: str  | None = None
    name:    str  | None = None
    profile: dict | None = None
    interview_id: str | None = None

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
    "lifeSatisfaction": False
} 