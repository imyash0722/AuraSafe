from __future__ import annotations

from typing import Any


# Environmental hazard knowledge base (adapted from green_score/green_score.py).
ENVIRONMENTAL_DB: dict[str, dict[str, str]] = {
    # Water / oceans
    "paraben": {"level": "High", "element": "Water", "color": "red", "tip": "Vitamin E"},
    "oxybenzone": {"level": "Extreme", "element": "Water/Reefs", "color": "red", "tip": "Zinc Oxide"},
    "triclosan": {"level": "High", "element": "Water", "color": "red", "tip": "Plain Soap"},
    "sulfates": {"level": "Moderate", "element": "Water", "color": "orange", "tip": "Decyl Glucoside"},
    "phosphates": {"level": "High", "element": "Water", "color": "red", "tip": "Phosphate-free"},
    "microplastics": {"level": "Extreme", "element": "Oceans", "color": "red", "tip": "Natural Fibers"},
    # Soil
    "pfas": {"level": "Extreme", "element": "Soil/Water", "color": "red", "tip": "Stainless Steel"},
    "glyphosate": {"level": "High", "element": "Soil/Bees", "color": "red", "tip": "Organic Mulch"},
    "lead": {"level": "Extreme", "element": "Soil", "color": "red", "tip": "Lead-free certified"},
    "imidacloprid": {"level": "Extreme", "element": "Soil/Insects", "color": "red", "tip": "Neem Oil"},
    "atrazine": {"level": "High", "element": "Groundwater", "color": "red", "tip": "Crop rotation"},
    "diclofenac": {"level": "High", "element": "Soil/Wildlife", "color": "orange", "tip": "Meloxicam"},
    # Air / indoor
    "phthalates": {"level": "High", "element": "Air/Indoor", "color": "red", "tip": "Glass/Essential Oils"},
    "ammonia": {"level": "Moderate", "element": "Air", "color": "orange", "tip": "White Vinegar"},
    "toluene": {"level": "High", "element": "Air/Smog", "color": "red", "tip": "Water-based solvents"},
    "butane": {"level": "Moderate", "element": "Atmosphere", "color": "orange", "tip": "Manual Pump"},
    "formaldehyde": {"level": "High", "element": "Air/Indoor", "color": "red", "tip": "NAF certified wood"},
    "cfcs": {"level": "Extreme", "element": "Ozone", "color": "red", "tip": "Natural refrigerants"},
}


def _split_ingredients(ingredients_text: str) -> list[str]:
    if not ingredients_text:
        return []
    raw = ingredients_text.replace(";", ",").replace("|", ",")
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def calculate_eco_grade(hazard_count: int) -> tuple[str, str]:
    """Returns (grade, color_key) where color_key is one of green/lightgreen/yellow/orange/red."""
    if hazard_count <= 0:
        return ("A", "green")
    if hazard_count <= 1:
        return ("B", "lightgreen")
    if hazard_count <= 2:
        return ("C", "yellow")
    if hazard_count <= 4:
        return ("D", "orange")
    return ("E", "red")


def score_environmental_impact(ingredients_text: str) -> dict[str, Any]:
    """
    Returns environmental breakdown based on direct and partial keyword matching.
    """
    ingredients = _split_ingredients(ingredients_text)
    matched: list[dict[str, str]] = []
    seen = set()

    for item in ingredients:
        for hazard_key, meta in ENVIRONMENTAL_DB.items():
            if hazard_key in item:
                unique = (item, hazard_key)
                if unique in seen:
                    continue
                seen.add(unique)
                matched.append(
                    {
                        "ingredient": item,
                        "hazard": hazard_key,
                        "level": meta["level"],
                        "element": meta["element"],
                        "tip": meta["tip"],
                        "color": meta["color"],
                    }
                )

    hazard_count = len(matched)
    grade, grade_color = calculate_eco_grade(hazard_count)
    return {
        "eco_grade": grade,
        "eco_grade_color": grade_color,
        "eco_hazard_count": hazard_count,
        "eco_hazards": matched,
    }
