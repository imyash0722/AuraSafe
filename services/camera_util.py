"""
Cross-platform camera and image decoding helpers for AuraSafe.

Desktop:
- Supports live camera scanning with OpenCV.

Android:
- Live OpenCV camera is not used.
- Image-based decode helpers are used by the UI flow (FilePicker capture/select).
"""

import platform
import re
from typing import Optional


def is_android() -> bool:
    try:
        return platform.system() == "Android"
    except Exception:
        return False


def cv2_available() -> bool:
    try:
        import cv2  # noqa: F401

        return True
    except ImportError:
        return False


def scan_barcode_from_camera(timeout_frames: int = 300) -> str | None:
    """
    Open default camera and decode a barcode/QR from live feed.
    On desktop, shows a preview window; press Q or ESC to cancel.
    Returns decoded string or None.
    """
    if is_android():
        return None
    try:
        import cv2
    except ImportError:
        return None

    cap = None
    win_name = "AuraSafe Barcode Scanner (Press Q / ESC to close)"
    try:
        # Prefer DirectShow backend on Windows for more reliable webcam startup.
        if platform.system() == "Windows" and hasattr(cv2, "CAP_DSHOW"):
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None

        use_bd = hasattr(cv2, "barcode") and hasattr(cv2.barcode, "BarcodeDetector")
        bd = cv2.barcode.BarcodeDetector() if use_bd else None
        qd = cv2.QRCodeDetector()

        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win_name, 960, 540)

        for _ in range(timeout_frames):
            ret, frame = cap.read()
            if not ret:
                break

            # Draw guide overlay for better alignment.
            h, w = frame.shape[:2]
            x1, y1 = int(w * 0.15), int(h * 0.2)
            x2, y2 = int(w * 0.85), int(h * 0.8)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 255), 2)
            cv2.putText(
                frame,
                "Align barcode/QR in box. Q or ESC to cancel.",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 220, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(win_name, frame)

            if bd is not None:
                try:
                    ok, decoded_info, _, _ = bd.detectAndDecodeWithType(frame)
                    if ok and decoded_info:
                        for val in decoded_info:
                            if val:
                                return val
                except Exception:
                    pass
            try:
                data, _, _ = qd.detectAndDecode(frame)
                if data:
                    return data
            except Exception:
                pass

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                return None
        return None
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
        try:
            import cv2

            cv2.destroyWindow(win_name)
        except Exception:
            pass


def scan_qr_from_camera(timeout_frames: int = 300) -> str | None:
    """
    Open default camera and decode a QR code from live feed.
    On desktop, shows a preview window; press Q or ESC to cancel.
    Returns decoded string or None.
    """
    if is_android():
        return None
    try:
        import cv2
    except ImportError:
        return None

    cap = None
    win_name = "AuraSafe MediQR Scanner (Press Q / ESC to close)"
    try:
        if platform.system() == "Windows" and hasattr(cv2, "CAP_DSHOW"):
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None

        qd = cv2.QRCodeDetector()
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win_name, 960, 540)

        for _ in range(timeout_frames):
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            x1, y1 = int(w * 0.2), int(h * 0.15)
            x2, y2 = int(w * 0.8), int(h * 0.85)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 140), 2)
            cv2.putText(
                frame,
                "Align MediQR in box. Q or ESC to cancel.",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 140),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(win_name, frame)

            try:
                data, _, _ = qd.detectAndDecode(frame)
                if data:
                    return data
            except Exception:
                pass

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                return None
        return None
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
        try:
            import cv2

            cv2.destroyWindow(win_name)
        except Exception:
            pass


def read_image_bytes(path: str) -> bytes | None:
    if not path:
        return None
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return None


def _extract_candidate_numbers(text: str) -> list[str]:
    """
    Extract likely UPC/EAN/GTIN candidates from text.
    Accepts 8-14 digits to cover common barcode lengths.
    """
    if not text:
        return []
    found = re.findall(r"(?<!\d)(\d{8,14})(?!\d)", text)
    seen = set()
    out = []
    for val in found:
        if val not in seen:
            seen.add(val)
            out.append(val)
    return out


def extract_possible_barcode_from_text(text: str) -> Optional[str]:
    candidates = _extract_candidate_numbers(text or "")
    if not candidates:
        return None
    preferred_lengths = (13, 12, 14, 8, 11, 10)
    for ln in preferred_lengths:
        for c in candidates:
            if len(c) == ln:
                return c
    return candidates[0]


def decode_barcode_zxing(image_path: str) -> str | None:
    """
    Decode any barcode/QR from an image file using zxingcpp (cross-platform,
    no native OpenCV required).  Works on Android.
    """
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        import zxingcpp
        from PIL import Image as _Image

        img = _Image.open(image_path).convert("RGB")
        results = zxingcpp.read_barcodes(img)
        if results:
            return results[0].text or None
    except Exception:
        pass
    return None


def decode_qr_zxing(image_path: str) -> str | None:
    """QR-specific decode via zxingcpp. Falls back to any barcode type."""
    return decode_barcode_zxing(image_path)


def decode_barcode_from_image_bytes(image_bytes: bytes) -> str | None:
    """
    Decode barcode/QR from raw image bytes using OpenCV when available.
    Returns decoded value or None.
    """
    if not image_bytes:
        return None
    try:
        import cv2
        import numpy as np
    except Exception:
        return None

    try:
        arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return None

        use_bd = hasattr(cv2, "barcode") and hasattr(cv2.barcode, "BarcodeDetector")
        if use_bd:
            try:
                bd = cv2.barcode.BarcodeDetector()
                ok, decoded_info, _, _ = bd.detectAndDecodeWithType(frame)
                if ok and decoded_info:
                    for val in decoded_info:
                        if val:
                            return val
            except Exception:
                pass

        try:
            qd = cv2.QRCodeDetector()
            data, _, _ = qd.detectAndDecode(frame)
            if data:
                return data
        except Exception:
            pass
    except Exception:
        return None

    return None


def decode_barcode_from_image_path(path: str) -> str | None:
    raw = read_image_bytes(path)
    if not raw:
        return None
    return decode_barcode_from_image_bytes(raw)


def decode_qr_from_image_bytes(image_bytes: bytes) -> str | None:
    if not image_bytes:
        return None
    try:
        import cv2
        import numpy as np

        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        qd = cv2.QRCodeDetector()
        data, _, _ = qd.detectAndDecode(img)
        return data or None
    except Exception:
        return None


def decode_qr_from_image_path(path: str) -> str | None:
    raw = read_image_bytes(path)
    if not raw:
        return None
    return decode_qr_from_image_bytes(raw)


def guess_barcode_from_file_metadata(file_name: str = "", file_path: str = "") -> str | None:
    """
    Last-resort Android fallback when direct image decode is unavailable.
    """
    combined = " ".join([file_name or "", file_path or ""])
    return extract_possible_barcode_from_text(combined)
