import requests
from typing import Optional


OFF_API = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

ALLERGEN_MAP = {
    "en:gluten": "Gluten", "en:wheat": "Wheat", "en:rye": "Rye",
    "en:barley": "Barley", "en:oats": "Oats", "en:milk": "Milk (Dairy)",
    "en:eggs": "Eggs", "en:egg": "Eggs", "en:peanuts": "Peanuts",
    "en:peanut": "Peanuts", "en:soybeans": "Soy", "en:soy": "Soy",
    "en:nuts": "Tree Nuts", "en:almonds": "Almonds", "en:cashews": "Cashews",
    "en:walnuts": "Walnuts", "en:fish": "Fish", "en:shellfish": "Shellfish",
    "en:crustaceans": "Crustaceans", "en:sesame": "Sesame", "en:mustard": "Mustard",
    "en:celery": "Celery", "en:lupin": "Lupin", "en:molluscs": "Molluscs",
    "en:sulphur-dioxide-and-sulphites": "Sulphites",
}


def fetch_product(barcode: str, timeout: int = 10) -> Optional[dict]:
    try:
        url = OFF_API.format(barcode=barcode)
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "AuraSafe/1.0"})
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("status") != 1:
            return None
        p = data.get("product", {})
        return _normalize(p, barcode)
    except Exception:
        return None


def _normalize(p: dict, barcode: str) -> dict:
    # Parse allergens
    allergen_tags = p.get("allergens_tags", []) + p.get("traces_tags", [])
    allergens = list({
        ALLERGEN_MAP[tag] for tag in allergen_tags if tag in ALLERGEN_MAP
    })

    # Parse additives (E-numbers)
    additives = [a.replace("en:", "").upper() for a in p.get("additives_tags", [])]

    # Ingredient text
    ingredients_text = (
        p.get("ingredients_text_en")
        or p.get("ingredients_text")
        or ""
    )

    # Image
    images = p.get("selected_images", {})
    image_url = (
        p.get("image_front_url")
        or p.get("image_url")
        or ""
    )

    # Nutrition grade
    nutri_grade = p.get("nutrition_grades", "").upper() or "?"

    return {
        "barcode": barcode,
        "title": p.get("product_name") or p.get("product_name_en") or "Unknown Product",
        "brand": p.get("brands", "Unknown Brand"),
        "category": p.get("categories", ""),
        "ingredients_text": ingredients_text,
        "allergens": allergens,
        "additives": additives,
        "nutri_grade": nutri_grade,
        "image_url": image_url,
        "labels": p.get("labels", ""),
        "quantity": p.get("quantity", ""),
        "countries": p.get("countries", ""),
        "source": "Open Food Facts",
    }
