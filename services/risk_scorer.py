from services.cpdat_matcher import match_ingredients_list
from services.green_score import score_environmental_impact
from typing import Optional

# Weights
W_HEALTH = 0.50
W_ENV = 0.30
W_PERSONAL = 0.20

VERDICTS = {
    range(1, 4): ("SAFE", "#4CAF50"),
    range(4, 7): ("CAUTION", "#FF9800"),
    range(7, 11): ("DANGER", "#F44336"),
}

# Conditions/diseases that map to ingredient risk triggers
CONDITION_TRIGGERS = {
    "diabetes": ["sugar", "high fructose corn syrup", "sucrose", "glucose", "dextrose", "maltose"],
    "hypertension": ["sodium", "salt", "sodium chloride", "sodium benzoate", "monosodium glutamate", "msg"],
    "celiac disease": ["gluten", "wheat", "barley", "rye", "oats"],
    "lactose intolerance": ["lactose", "milk", "cream", "whey", "casein"],
    "pku": ["aspartame", "phenylalanine"],
    "kidney disease": ["potassium chloride", "phosphate", "sodium", "protein"],
    "heart disease": ["trans fat", "partially hydrogenated", "sodium", "cholesterol"],
    "asthma": ["sulfur dioxide", "sulphites", "sodium benzoate", "tartrazine", "yellow 5"],
}


def score_product(product: dict, user_profile: dict) -> dict:
    ingredients_text = product.get("ingredients_text", "")
    off_allergens = [a.lower() for a in product.get("allergens", [])]
    user_allergies = [a.lower() for a in user_profile.get("allergies", [])]
    user_conditions = [c.lower() for c in user_profile.get("conditions", [])]

    # Match CPDat
    ingredient_matches = match_ingredients_list(ingredients_text)

    # Compute health & env scores from matched ingredients
    known = [m for m in ingredient_matches if m["health_score"] is not None]
    if known:
        avg_health = sum(m["health_score"] for m in known) / len(known)
        max_health = max(m["health_score"] for m in known)
        avg_env = sum(m["env_score"] for m in known) / len(known)
        max_env = max(m["env_score"] for m in known)
        # Blend avg + max (penalise worst offenders)
        health_score = round(avg_health * 0.6 + max_health * 0.4)
        env_score = round(avg_env * 0.6 + max_env * 0.4)
        confidence = "HIGH" if len(known) >= 3 else "MEDIUM"
    else:
        health_score = 5
        env_score = 3
        confidence = "LOW"

    # Personal risk
    personal_alerts = []
    personal_risk = "SAFE"

    # Check user allergies vs OFF allergens and ingredients text
    ingr_low = ingredients_text.lower()
    for allergy in user_allergies:
        if allergy in off_allergens or allergy in ingr_low:
            personal_alerts.append(f"⚠️ Contains {allergy.title()} — matches your allergy")
            personal_risk = "UNSAFE_FOR_YOU"

    # Check user conditions vs condition triggers
    for condition in user_conditions:
        triggers = CONDITION_TRIGGERS.get(condition, [])
        for trigger in triggers:
            if trigger in ingr_low:
                personal_alerts.append(f"⚠️ Contains {trigger.title()} — concern for {condition.title()}")
                if personal_risk == "SAFE":
                    personal_risk = "CAUTION"

    # If personal risk is unsafe, bump personal score to 10
    personal_score_raw = 10 if personal_risk == "UNSAFE_FOR_YOU" else (6 if personal_risk == "CAUTION" else 2)

    # Overall score
    if known:
        overall = round(
            health_score * W_HEALTH +
            env_score * W_ENV +
            personal_score_raw * W_PERSONAL
        )
    else:
        overall = 5  # neutral unknown

    overall = max(1, min(10, overall))
    health_score = max(1, min(10, health_score))
    env_score = max(1, min(10, env_score))

    verdict, verdict_color = _get_verdict(overall)

    return {
        "overall": overall,
        "health_score": health_score,
        "env_score": env_score,
        "green_score": score_environmental_impact(ingredients_text),
        "personal_risk": personal_risk,
        "personal_alerts": personal_alerts,
        "verdict": verdict,
        "verdict_color": verdict_color,
        "confidence": confidence,
        "ingredient_details": ingredient_matches,
        "num_ingredients_matched": len(known),
        "num_ingredients_total": len(ingredient_matches),
    }


def _get_verdict(score: int) -> tuple:
    if score <= 3:
        return "SAFE", "#4CAF50"
    elif score <= 6:
        return "CAUTION", "#FF9800"
    else:
        return "DANGER", "#F44336"


def get_disposal_guidance(product: dict, score_result: dict) -> list:
    guidance = []
    ingr_low = (product.get("ingredients_text") or "").lower()
    category = (product.get("category") or "").lower()

    if any(f in ingr_low for f in ["triclosan", "bleach", "sodium hypochlorite"]):
        guidance.append("🚫 Do not pour down drain — harmful to aquatic life. Dispose at hazardous waste facility.")
    if any(f in ingr_low for f in ["battery", "mercury", "lead"]):
        guidance.append("🔋 Contains heavy metals — take to e-waste or hazardous waste collection point.")
    if "paint" in category or "solvent" in category:
        guidance.append("🎨 Don't throw in regular trash. Take to local hazardous household waste site.")
    if score_result["env_score"] >= 7:
        guidance.append("♻️ High environmental impact — check local hazardous disposal options.")
    if not guidance:
        guidance.append("✅ Can be disposed of with regular household waste. Rinse containers before recycling.")

    return guidance
