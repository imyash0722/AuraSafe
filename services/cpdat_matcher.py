import json
import os
import re
import difflib
from typing import Optional

_CPDAT: dict = {}
_LOADED = False

CPDAT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "assets", "cpdat_hazards.json"
)


def load_cpdat():
    global _CPDAT, _LOADED
    if _LOADED:
        return
    try:
        with open(CPDAT_PATH, "r", encoding="utf-8") as f:
            _CPDAT = json.load(f)
        _LOADED = True
    except Exception as e:
        print(f"[CPDat] Failed to load: {e}")
        _CPDAT = {}
        _LOADED = True


def match_ingredient(name: str) -> dict:
    load_cpdat()
    if not name or not _CPDAT:
        return _unknown()

    name_lc = name.strip().lower()

    # 1. Exact match on primary key
    if name_lc in _CPDAT:
        entry = _CPDAT[name_lc]
        return _result(entry, "exact", name_lc)

    # 2. Synonym match
    for key, entry in _CPDAT.items():
        synonyms = [s.lower() for s in entry.get("synonyms", [])]
        if name_lc in synonyms:
            return _result(entry, "synonym", key)

    # 3. Substring match (ingredient list may contain "sodium lauryl sulfate (SLS)")
    for key, entry in _CPDAT.items():
        if key in name_lc or name_lc in key:
            return _result(entry, "partial", key)
        for syn in entry.get("synonyms", []):
            if syn.lower() in name_lc or name_lc in syn.lower():
                return _result(entry, "partial", key)

    # 4. Fuzzy match with cutoff
    all_keys = list(_CPDAT.keys())
    all_synonyms = []
    key_for_syn = {}
    for key, entry in _CPDAT.items():
        for syn in entry.get("synonyms", []):
            sl = syn.lower()
            all_synonyms.append(sl)
            key_for_syn[sl] = key

    candidates = all_keys + all_synonyms
    matches = difflib.get_close_matches(name_lc, candidates, n=1, cutoff=0.75)
    if matches:
        match_str = matches[0]
        key = match_str if match_str in _CPDAT else key_for_syn.get(match_str)
        if key and key in _CPDAT:
            return _result(_CPDAT[key], "fuzzy", key)

    return _unknown()


def match_ingredients_list(ingredients_text: str) -> list:
    if not ingredients_text:
        return []
    parts = re.split(r"[,;\(\)\[\]]", ingredients_text)
    results = []
    seen = set()
    for part in parts:
        part = part.strip().strip(".")
        if len(part) < 3 or part.lower() in seen:
            continue
        seen.add(part.lower())
        result = match_ingredient(part)
        result["ingredient"] = part
        results.append(result)
    return results


def _result(entry: dict, confidence: str, matched_key: str) -> dict:
    return {
        "health_score": entry.get("health_score", 5),
        "env_score": entry.get("env_score", 3),
        "hazard_flags": entry.get("hazard_flags", []),
        "cas": entry.get("cas", ""),
        "matched_as": matched_key,
        "confidence": confidence,
    }


def _unknown() -> dict:
    return {
        "health_score": None,
        "env_score": None,
        "hazard_flags": [],
        "cas": "",
        "matched_as": None,
        "confidence": "unknown",
    }
