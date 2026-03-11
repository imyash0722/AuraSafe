import requests
from typing import Optional


BL_API = "https://api.barcodelookup.com/v3/products"


def fetch_product(barcode: str, api_key: str, timeout: int = 10) -> Optional[dict]:
    if not api_key or api_key.strip() == "":
        return None
    try:
        resp = requests.get(
            BL_API,
            params={"barcode": barcode, "formatted": "y", "key": api_key},
            timeout=timeout,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        products = data.get("products", [])
        if not products:
            return None
        p = products[0]
        return {
            "barcode": barcode,
            "title": p.get("title", ""),
            "brand": p.get("brand", ""),
            "category": p.get("category", ""),
            "ingredients_text": p.get("ingredients", ""),
            "image_url": p.get("images", [""])[0] if p.get("images") else "",
            "description": p.get("description", ""),
            "source": "BarcodeLookup",
        }
    except Exception:
        return None


def merge_with_off(off_data: dict, bl_data: Optional[dict]) -> dict:
    if not bl_data:
        return off_data
    merged = dict(off_data)
    # Fill gaps from barcode lookup
    if not merged.get("title") or merged["title"] == "Unknown Product":
        merged["title"] = bl_data.get("title") or merged["title"]
    if not merged.get("brand") or merged["brand"] == "Unknown Brand":
        merged["brand"] = bl_data.get("brand") or merged["brand"]
    if not merged.get("ingredients_text"):
        merged["ingredients_text"] = bl_data.get("ingredients_text", "")
    if not merged.get("image_url"):
        merged["image_url"] = bl_data.get("image_url", "")
    merged["sources"] = ["Open Food Facts", "BarcodeLookup"]
    return merged
