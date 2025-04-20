
AGGREGATE_DATA = {
    # Age distribution bins (dist_age)
    "age": {
        "distribution": [
            {"label": "18-24", "start": 18, "end": 24, "percentage": 15.5},
            {"label": "25-34", "start": 25, "end": 34, "percentage": 35.2},
            {"label": "35-44", "start": 35, "end": 44, "percentage": 25.8},
            {"label": "45-54", "start": 45, "end": 54, "percentage": 13.5},
            {"label": "55-64", "start": 55, "end": 64, "percentage": 7.0},
            {"label": "65+",   "start": 65, "end": None, "percentage": 3.0},
        ],
    },

    # lifeStage distribution (dist_life_stage)
    # Map schema keys to CSV categories
    "lifeStage": {
        "mapping": {
            "education/training": {"label": "Education/Training", "pct": 12.0},
            "early career":       {"label": "Early Career",        "pct": 38.5},
            "established career": {"label": "Established Career",  "pct": 30.5},
            "family formation":   {"label": "Building Family",     "pct": 10.0},
            "empty nest":         {"label": "Empty Nest",          "pct": 5.0},
            "retirement preparation": {"label": "Retirement Prep", "pct": 4.0},
        }
    },

    # livingArrangement distribution (dist_living_situation)
    "livingArrangement": {
        "mapping": {
            "alone":     {"label": "Solo",      "pct": 22},
            "roommates": {"label": "Roommates", "pct": 15},
            "partner":   {"label": "Partner",   "pct": 45},
            "family":    {"label": "Family",    "pct": 18},
            "other":     {"label": None,        "pct": 0},  # No direct CSV data
        }
    },

    # location distribution (dist_geographic)
    "location": {
        "mapping": {
            "urban":    {"label": "Urban",    "pct": 48},
            "suburban": {"label": "Suburban", "pct": 37},
            "rural":    {"label": "Rural",    "pct": 15},
        }
    },

    # educationLevel distribution (dist_education)
    "educationLevel": {
        "mapping": {
            # (You can free-form compare; not all users have these exact strings.)
            # Example categories from CSV:
            "High School":  {"label": "High School",  "pct": 15},
            "Some College": {"label": "Some College", "pct": 25},
            "Bachelors":    {"label": "Bachelors",    "pct": 40},
            "Graduate":     {"label": "Graduate",     "pct": 20},
        }
    },

    # careerField distribution (dist_career_field)
    "careerField": {
        "mapping": {
            "Technology": {"label": "Technology", "pct": 25},
            "Healthcare": {"label": "Healthcare", "pct": 20},
            "Education":  {"label": "Education",  "pct": 15},
            "Business/Finance": {"label": "Business/Finance", "pct": 20},
            "Other":      {"label": "Other",      "pct": 20},
        }
    },

    # financialStability => has both average + distribution
    "financialStability": {
        "average": 6.2,
        "distribution": [
            {"label": "1-2",  "start": 1, "end": 2,  "pct": 5},
            {"label": "3-4",  "start": 3, "end": 4,  "pct": 15},
            {"label": "5-6",  "start": 5, "end": 6,  "pct": 40},
            {"label": "7-8",  "start": 7, "end": 8,  "pct": 30},
            {"label": "9-10", "start": 9, "end": 10, "pct": 10},
        ],
    },

    # socialConnection distribution (dist_social_connection)
    "socialConnection": {
        "mapping": {
            "very strong": {"label": "Very Strong", "pct": 35},
            "adequate":     {"label": "Adequate",    "pct": 55},
            "limited":      {"label": "Limited",     "pct": 10},
        }
    },

    # healthConfidence => average only (avg_health_confidence = 5.8)
    "healthConfidence": {
        "average": 5.8
    },

    # lifeSatisfaction => average only (avg_life_satisfaction = 7.1)
    "lifeSatisfaction": {
        "average": 7.1
    },
}


DEFAULT_PROGRESS = {
    'age': False,
    'lifeStage': False,
    'livingArrangement': False,
    'location': False,
    'educationLevel': False,
    'careerField': False,
    'financialStability': False,
    'socialConnection': False,
    'healthConfidence': False,
    'lifeSatisfaction': False,
}
