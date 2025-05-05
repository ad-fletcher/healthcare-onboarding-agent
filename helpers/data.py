
AGGREGATE_DATAphase1 = {
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
            "other":     {"label": 'Other',        "pct": 0},  # No direct CSV data
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

DEFAULT_PROGRESSphase1 = {
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



# ═════════════════════════════  Phase 2 – Risk Tolerance  ═════════════════════════════
AGGREGATE_DATAphase2 = {
    "safetyEquipmentUsage": {
        "mapping": {
            "always":    {"label": "Always",    "pct": 30},
            "sometimes": {"label": "Sometimes", "pct": 45},
            "rarely":    {"label": "Rarely",    "pct": 20},
            "never":     {"label": "Never",     "pct": 5},
        }
    },
    "treatmentPreference": {
        "mapping": {
            "physical_therapy": {"label": "Physical Therapy First", "pct": 60},
            "injection":        {"label": "Injection First",        "pct": 10},
            "surgery":          {"label": "Surgical Option First",  "pct": 5},
            "self_manage":      {"label": "Self‑Manage First",      "pct": 25},
        }
    },
    "headacheStrategy": {
        "mapping": {
            "medication_immediately": {"label": "Medicate Immediately", "pct": 40},
            "wait_and_see":           {"label": "Wait & See",           "pct": 35},
            "non_medication_first":   {"label": "Non‑Medication First", "pct": 25},
        }
    },
    "newTreatmentOpenness": {
        "mapping": {
            "try_immediately":        {"label": "Try Immediately",      "pct": 18},
            "wait_until_established": {"label": "Wait Until Proven",    "pct": 58},
            "stick_with_traditional": {"label": "Stick With Traditional","pct": 24},
        }
    },
    "financialRisk": {
        "mapping": {
            "willing":   {"label": "Willing to Pay", "pct": 22},
            "maybe":     {"label": "Maybe/Depends",  "pct": 48},
            "unwilling": {"label": "Unwilling",      "pct": 30},
        }
    },
    "preventiveCareAttitude": {
        "mapping": {
            "on_schedule":        {"label": "On Schedule",        "pct": 42},
            "when_convenient":    {"label": "When Convenient",    "pct": 38},
            "only_when_symptoms": {"label": "Only w/ Symptoms",   "pct": 20},
        }
    },
    "infoVerificationStyle": {
        "mapping": {
            "adopt_immediately": {"label": "Adopt Immediately", "pct": 12},
            "research_first":    {"label": "Research First",    "pct": 63},
            "ask_provider":      {"label": "Ask Provider",      "pct": 25},
        }
    },
    "chestPainResponse": {
        "mapping": {
            "call_ems":          {"label": "Call EMS",          "pct": 18},
            "urgent_appointment":{"label": "Urgent Appointment","pct": 52},
            "wait_and_see":      {"label": "Wait & See",        "pct": 30},
        }
    },
    "altMedicineOpenness": {
        "mapping": {
            "eager":         {"label": "Very Open",      "pct": 20},
            "somewhat_open": {"label": "Somewhat Open",  "pct": 55},
            "not_open":      {"label": "Not Open",       "pct": 25},
        }
    },
    "geneticTestingAttitude": {
        "mapping": {
            "eager_to_know":        {"label": "Eager to Know",        "pct": 28},
            "cautiously_interested":{"label": "Cautiously Interested","pct": 50},
            "prefer_not_to_know":   {"label": "Prefer Not to Know",   "pct": 22},
        }
    },
}

DEFAULT_PROGRESSphase2 = {
    'safetyEquipmentUsage':   False,
    'treatmentPreference':    False,
    'headacheStrategy':       False,
    'newTreatmentOpenness':   False,
    'financialRisk':          False,
    'preventiveCareAttitude': False,
    'infoVerificationStyle':  False,
    'chestPainResponse':      False,
    'altMedicineOpenness':    False,
    'geneticTestingAttitude': False,
}


# ═════════════════════════════  Phase 3 – Vitality Signs  ═════════════════════════════
AGGREGATE_DATAphase3 = {
    "healthVision": {
        "mapping": {
            "mobility/independence focus": {"label": "Mobility Focus",  "pct": 35},
            "energy/vitality focus":       {"label": "Energy Focus",    "pct": 25},
            "prevention focus":            {"label": "Prevention",      "pct": 20},
            "balanced focus":              {"label": "Balanced",        "pct": 15},
            "other":                       {"label": "Other",           "pct": 5},
        }
    },
    "moneyRelationship": {
        "mapping": {
            "frugal":       {"label": "Frugal",       "pct": 30},
            "balanced":     {"label": "Balanced",     "pct": 55},
            "spendthrift":  {"label": "Spendthrift",  "pct": 15},
        }
    },
    "timeRelationship": {
        "mapping": {
            "investment": {"label": "Investment", "pct": 45},
            "neutral":    {"label": "Neutral",    "pct": 35},
            "burden":     {"label": "Burden",     "pct": 20},
        }
    },
    "agingRelationship": {
        "mapping": {
            "acceptance": {"label": "Acceptance", "pct": 48},
            "avoidance":  {"label": "Avoidance",  "pct": 32},
            "worry":      {"label": "Worry",      "pct": 20},
        }
    },
    "parentInfluence": {
        "mapping": {
            "learn_from_mistakes": {"label": "Learn From Mistakes", "pct": 60},
            "follow_example":      {"label": "Follow Example",      "pct": 15},
            "neutral":             {"label": "Neutral",             "pct": 10},
            "complex":             {"label": "Complex",             "pct": 10},
            "other":               {"label": "Other",               "pct": 5},
        }
    },
    "jobImpact": {
        "mapping": {
            "stress/inactivity": {"label": "Stress/Inactivity", "pct": 50},
            "well‑being_source": {"label": "Positive Source",   "pct": 18},
            "mixed":             {"label": "Mixed Impact",      "pct": 22},
            "minimal":           {"label": "Minimal Impact",    "pct": 10},
            "other":             {"label": "Other",             "pct": 0},
        }
    },
    "foodRelationship": {
        "mapping": {
            "fuel_first":     {"label": "Fuel First",     "pct": 30},
            "balanced":       {"label": "Balanced",       "pct": 45},
            "pleasure_first": {"label": "Pleasure First", "pct": 25},
            "other":          {"label": "Other",          "pct": 0},
        }
    },
    "techRelationship": {
        "mapping": {
            "mainly_tool":        {"label": "Mainly Tool",        "pct": 40},
            "mixed":              {"label": "Mixed",              "pct": 45},
            "mostly_distraction": {"label": "Mostly Distraction", "pct": 15},
            "other":              {"label": "Other",              "pct": 0},
        }
    },
    "vanityRelationship": {
        "mapping": {
            "primary":   {"label": "Primary Motivator",   "pct": 18},
            "secondary": {"label": "Secondary Benefit",   "pct": 55},
            "minimal":   {"label": "Minimal",             "pct": 27},
            "other":     {"label": "Other",               "pct": 0},
        }
    },
    "mortalityPerspective": {
        "mapping": {
            "motivator":          {"label": "Strong Motivator",  "pct": 25},
            "occasional_thought": {"label": "Occasional Thought","pct": 55},
            "avoidant":           {"label": "Avoidant",          "pct": 20},
            "other":              {"label": "Other",             "pct": 0},
        }
    },
}

DEFAULT_PROGRESSphase3 = {
    'healthVision':         False,
    'moneyRelationship':    False,
    'timeRelationship':     False,
    'agingRelationship':    False,
    'parentInfluence':      False,
    'jobImpact':            False,
    'foodRelationship':     False,
    'techRelationship':     False,
    'vanityRelationship':   False,
    'mortalityPerspective': False,
}


# ═════════════════════════════  Phase 4 – Medical Profile  ═════════════════════════════
AGGREGATE_DATAphase4 = {
    "currentMedications": {
        "mapping": {
            True:  {"label": "Takes Regular Meds", "pct": 38},
            False: {"label": "No Regular Meds",    "pct": 62},
        }
    },
    "conditions": {
        "mapping": {
            True:  {"label": "Has Conditions", "pct": 29},
            False: {"label": "None Reported",  "pct": 71},
        }
    },
    "surgeries": {
        "mapping": {
            True:  {"label": "Has Surgical History", "pct": 22},
            False: {"label": "No Surgeries",         "pct": 78},
        }
    },
    "emergencyVisits": {
        "mapping": {
            True:  {"label": "Visited ER/Urgent Care", "pct": 26},
            False: {"label": "No Visits",             "pct": 74},
        }
    },
    "lastCheckup": {
        "mapping": {
            "within 1 year":  {"label": "< 1 yr",        "pct": 48},
            "1-2 years ago":  {"label": "1‑2 yrs",       "pct": 28},
            ">2 years":       {"label": "> 2 yrs",       "pct": 18},
            "never/unsure":   {"label": "Never/Unsure",  "pct": 6},
        }
    },
    "familyHistory": {
        "mapping": {
            True:  {"label": "Known History", "pct": 42},
            False: {"label": "No / Unsure",   "pct": 58},
        }
    },
    "mentalHealth": {
        "mapping": {
            "generally_good":          {"label": "Generally Good",      "pct": 46},
            "significant_challenges":  {"label": "Significant Issues",  "pct": 18},
            "consistently_good":       {"label": "Consistently Good",   "pct": 22},
            "prefer_not_to_say":       {"label": "Prefer Not to Say",   "pct": 14},
        }
    },
    "recordPermission": {
        "mapping": {
            True:  {"label": "Granted", "pct": 80},
            False: {"label": "Declined","pct": 20},
        }
    },
}

DEFAULT_PROGRESSphase4 = {
    'currentMedications': True,   # Ask “do you take any?” then mark done
    'conditions':         True,
    'surgeries':          True,
    'emergencyVisits':    True,
    'lastCheckup':        False,
    'familyHistory':      True,
    'mentalHealth':       False,
    'recordPermission':   False,
}
