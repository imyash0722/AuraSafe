from typing import Optional

# Symptom → urgency classification rules
# Each entry: (keywords_that_trigger, urgency_level, weight)
RED_SYMPTOMS = [
    "chest pain", "heart attack", "difficulty breathing", "cannot breathe",
    "shortness of breath", "unconscious", "unresponsive", "stroke",
    "severe bleeding", "not breathing", "choking", "seizure", "convulsion",
    "anaphylaxis", "severe allergic reaction", "loss of consciousness",
    "suicidal", "overdose", "poisoning", "paralysis", "severe burn",
]

YELLOW_SYMPTOMS = [
    "high fever", "fever above 39", "fever above 40", "persistent vomiting",
    "blood in urine", "blood in stool", "severe headache", "migraine",
    "broken bone", "fracture", "dislocation", "moderate pain",
    "dehydration", "can't keep fluids", "severe diarrhea", "fainting",
    "dizziness", "blurred vision", "chest tightness", "wheezing",
    "abdominal pain", "stomach pain", "ear pain", "eye pain",
    "urinary tract infection", "uti",
]

GREEN_SYMPTOMS = [
    "mild cold", "runny nose", "sneezing", "sore throat", "cough",
    "mild headache", "low-grade fever", "minor cut", "scrape", "bruise",
    "mild stomach upset", "nausea", "mild rash", "insect bite",
    "muscle ache", "back pain", "stress", "anxiety", "fatigue",
    "mild allergy", "hay fever", "constipation", "bloating",
]

ESCALATION_GUIDANCE = {
    "RED": "🚨 EMERGENCY — Call 112 immediately. Do not delay.",
    "YELLOW": "⚠️ Seek medical attention within a few hours. Visit a clinic or urgent care.",
    "GREEN": "✅ Monitor symptoms at home. Rest, stay hydrated. See a doctor if it worsens.",
}

DETAILED_GUIDANCE = {
    "chest pain": "Possible cardiac event. Chew aspirin if available and not allergic. Call 112 now.",
    "difficulty breathing": "Sit upright, loosen tight clothing. If inhaler available, use it. Call 112.",
    "seizure": "Clear the area. Do NOT restrain. Do not put anything in mouth. Time the seizure — call 112 if > 5 minutes or it's a first seizure.",
    "choking": "Perform Heimlich maneuver (abdominal thrusts). Call 112 if unsuccessful.",
    "anaphylaxis": "Use epinephrine auto-injector (EpiPen) if available. Call 112 immediately.",
    "severe bleeding": "Apply firm, direct pressure with a clean cloth. Elevate the limb. Call 112.",
    "unconscious": "Check breathing. If breathing, place in recovery position. Call 112.",
    "stroke": "Remember FAST: Face drooping, Arm weakness, Speech difficulty, Time to call 112.",
    "high fever": "Reduce fever with paracetamol/ibuprofen. Keep hydrated. See a doctor soon.",
}


def classify_symptoms(symptoms: list) -> dict:
    text = " ".join(s.lower() for s in symptoms)
    urgency = "GREEN"

    # Check RED first (highest priority)
    triggered_red = [s for s in RED_SYMPTOMS if s in text]
    triggered_yellow = [s for s in YELLOW_SYMPTOMS if s in text]
    triggered_green = [s for s in GREEN_SYMPTOMS if s in text]

    if triggered_red:
        urgency = "RED"
    elif triggered_yellow:
        urgency = "YELLOW"
    elif triggered_green:
        urgency = "GREEN"
    else:
        urgency = "GREEN"  # Default: conservative

    # Build specific guidance
    specific = []
    for sym in triggered_red + triggered_yellow:
        if sym in DETAILED_GUIDANCE:
            specific.append(DETAILED_GUIDANCE[sym])

    guidance = ESCALATION_GUIDANCE[urgency]
    if specific:
        guidance = specific[0]  # Most specific guidance first

    return {
        "urgency": urgency,
        "guidance": guidance,
        "general_guidance": ESCALATION_GUIDANCE[urgency],
        "escalate": urgency == "RED",
        "triggered_red": triggered_red,
        "triggered_yellow": triggered_yellow,
        "triggered_green": triggered_green,
        "disclaimer": "⚠️ AuraSafe is NOT a diagnostic tool. Always seek professional medical advice.",
    }


def get_urgency_color(urgency: str) -> str:
    return {"RED": "#F44336", "YELLOW": "#FF9800", "GREEN": "#4CAF50"}.get(urgency, "#9E9E9E")


def get_urgency_emoji(urgency: str) -> str:
    return {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}.get(urgency, "⚪")


COMMON_SYMPTOMS = [
    "Chest Pain", "Difficulty Breathing", "Fever", "High Fever",
    "Headache", "Nausea", "Vomiting", "Dizziness", "Seizure",
    "Unconscious", "Severe Bleeding", "Choking", "Stroke",
    "Sore Throat", "Cough", "Fatigue", "Back Pain", "Stomach Pain",
    "Rash", "Allergic Reaction", "Anaphylaxis", "Diarrhea",
    "Chest Tightness", "Wheezing", "Fracture",
]
