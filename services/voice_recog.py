from __future__ import annotations

import json
import os
import platform
import queue
import threading
from typing import Callable


DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "assets",
    "models",
    "vosk-model-small-en-us",
)


def is_android() -> bool:
    try:
        return platform.system() == "Android"
    except Exception:
        return False


def voice_stack_available() -> tuple[bool, str]:
    if is_android():
        return False, "Offline Vosk microphone capture is currently disabled on Android build."
    try:
        import sounddevice as sd
        from vosk import Model  # noqa: F401
    except Exception as exc:
        return (
            False,
            "Voice dependencies missing. Install with: "
            "pip install vosk sounddevice",
        )
    try:
        devices = sd.query_devices()
        if not devices:
            return False, "No audio input device detected."
        default_input = sd.default.device[0] if sd.default and sd.default.device else None
        if default_input is None or int(default_input) < 0:
            return False, "No default microphone set. Set one in OS sound settings."
    except Exception as exc:
        return False, f"Microphone check failed: {exc}"
    if not os.path.exists(DEFAULT_MODEL_PATH):
        return False, f"Vosk model missing at {DEFAULT_MODEL_PATH}"
    return True, "ready"


class VoiceService:
    """
    Desktop-oriented streaming speech recognition using Vosk + sounddevice.
    """

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or DEFAULT_MODEL_PATH
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Vosk model not found at: {self.model_path}")

        from vosk import Model

        self.model = Model(self.model_path)
        self.audio_queue: queue.Queue[bytes] = queue.Queue()
        self.stop_event = threading.Event()

    def _callback(self, indata, frames, time_info, status):
        # Keep feeding audio even when PortAudio reports non-fatal status flags.
        self.audio_queue.put(bytes(indata))

    def stream_text(self):
        import sounddevice as sd
        from vosk import KaldiRecognizer

        try:
            device_info = sd.query_devices(None, "input")
            samplerate = int(device_info.get("default_samplerate", 16000))
        except Exception:
            samplerate = 16000
        self.stop_event.clear()
        last_partial = ""

        with sd.RawInputStream(
            samplerate=samplerate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._callback,
        ):
            rec = KaldiRecognizer(self.model, samplerate)
            while not self.stop_event.is_set():
                try:
                    data = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if rec.AcceptWaveform(data):
                    text = json.loads(rec.Result()).get("text", "").strip()
                    if text:
                        last_partial = ""
                        yield ("final", text)
                else:
                    try:
                        partial = json.loads(rec.PartialResult()).get("partial", "").strip()
                    except Exception:
                        partial = ""
                    if partial and partial != last_partial:
                        last_partial = partial
                        yield ("partial", partial)

    def stop(self):
        self.stop_event.set()


def start_voice_capture(
    on_text: Callable[[str], None],
    on_error: Callable[[str], None],
    on_partial: Callable[[str], None] | None = None,
) -> Callable[[], None]:
    """
    Starts capture in a background thread and returns a stop() callable.
    """
    ok, reason = voice_stack_available()
    if not ok:
        on_error(reason)
        return lambda: None

    svc = VoiceService()

    def _runner():
        try:
            for kind, chunk in svc.stream_text():
                if kind == "partial":
                    if on_partial:
                        on_partial(chunk)
                else:
                    on_text(chunk)
        except Exception as exc:
            on_error(
                "Voice capture failed: "
                f"{exc}. Check Windows microphone privacy permissions and default input device."
            )

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    return svc.stop
