import json
import qrcode
import io
import base64
from PIL import Image
from typing import Optional

PROFILE_FIELDS = ["name", "dob", "blood_group", "allergies", "conditions", "medications", "emergency_contact"]


def generate_qr(profile: dict) -> str:
    """Returns base64 encoded PNG of the QR code."""
    payload = {k: profile.get(k, "") for k in PROFILE_FIELDS}
    payload_str = json.dumps(payload, separators=(",", ":"))

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(payload_str)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1A237E", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_qr_file(profile: dict) -> str:
    """Saves QR code PNG to a temp file and returns the file path."""
    import tempfile, os
    payload = {k: profile.get(k, "") for k in PROFILE_FIELDS}
    payload_str = json.dumps(payload, separators=(",", ":"))

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(payload_str)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1A237E", back_color="white")
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    tmp.close()
    return tmp.name


def decode_qr_data(raw_string: str) -> Optional[dict]:
    raw_string = raw_string.strip()
    try:
        data = json.loads(raw_string)
        # Ensure lists are lists
        for list_field in ["allergies", "conditions", "medications"]:
            if isinstance(data.get(list_field), str):
                data[list_field] = [x.strip() for x in data[list_field].split(",") if x.strip()]
        return data
    except (json.JSONDecodeError, TypeError):
        return None


def decode_qr_from_image(image_bytes: bytes) -> Optional[dict]:
    """Decodes a MediQR from raw image bytes using camera_util backends."""
    try:
        from services.camera_util import decode_qr_from_image_bytes

        raw = decode_qr_from_image_bytes(image_bytes)
        if not raw:
            return None
        return decode_qr_data(raw)
    except Exception as e:
        print(f"[MediQR] QR decode error: {e}")
        return None
