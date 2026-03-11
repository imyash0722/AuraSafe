

import os
import sys
import json
import queue
import threading    
import tkinter as tk
from tkinter import ttk, messagebox
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# --- PART 1: VOICE SERVICE LOGIC ---
class VoiceService:
    def __init__(self, model_path):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Vosk model not found at: {model_path}")
        
        self.model = Model(model_path)
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()

    def _callback(self, indata, frames, time, status):
        """Callback for the sounddevice input stream."""
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def start_listening(self):
        """Generator that yields recognized text chunks."""
        device_info = sd.query_devices(None, 'input')
        samplerate = int(device_info['default_samplerate'])
        self.stop_event.clear()
        
        with sd.RawInputStream(samplerate=samplerate, blocksize=8000, 
                               dtype='int16', channels=1, 
                               callback=self._callback):
            
            rec = KaldiRecognizer(self.model, samplerate)
            while not self.stop_event.is_set():
                try:
                    # Use timeout so the thread can exit if stop_event is set
                    data = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                    
                if rec.AcceptWaveform(data):
                    yield json.loads(rec.Result()).get("text", "")
                else:
                    # You can yield partial results here if you want real-time typing
                    pass

    def stop_listening(self):
        """Signals the listening thread to stop and clean up."""
        self.stop_event.set()

# --- PART 2: UI INTERFACE (SehatSathi) ---
class SehatSathiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AuraSafe - SehatSathi")
        self.root.geometry("450x350")
        self.root.configure(padx=20, pady=20)

        # UI Styling & Elements
        self.status_label = ttk.Label(root, text="System Ready", foreground="gray")
        self.status_label.pack(anchor="w")

        self.display_text = tk.Text(root, height=8, width=50, state="disabled", wrap="word")
        self.display_text.pack(pady=10)

        self.mic_button = ttk.Button(root, text="🎤 Start Listening", command=self.toggle_voice)
        self.mic_button.pack(pady=10)

        # Configuration
        # Pointing to your specific folder structure
        self.model_path = os.path.join("assets", "models", "vosk-model-small-en-us")
        self.is_listening = False
        self.voice_service = None

    def update_display(self, text):
        """Helper to thread-safely update the text box."""
        self.display_text.config(state="normal")
        self.display_text.insert("end", f"User: {text}\n")
        self.display_text.see("end")
        self.display_text.config(state="disabled")

    def toggle_voice(self):
        if not self.is_listening:
            try:
                if not self.voice_service:
                    self.status_label.config(text="Loading Model...", foreground="orange")
                    self.voice_service = VoiceService(self.model_path)
                
                self.is_listening = True
                self.mic_button.config(text="🛑 Stop Recording")
                self.status_label.config(text="Listening...", foreground="red")
                
                # Start background thread to prevent UI freezing
                threading.Thread(target=self.process_voice, daemon=True).start()
            except Exception as e:
                messagebox.showerror("Error", f"Could not start voice service: {e}")
        else:
            self.stop_voice()

    def stop_voice(self):
        self.is_listening = False
        if self.voice_service:
            self.voice_service.stop_listening()
        self.mic_button.config(text="🎤 Start Listening")
        self.status_label.config(text="System Ready", foreground="gray")

    def process_voice(self):
        """Loop that handles the speech-to-text results."""
        for text in self.voice_service.start_listening():
            if not self.is_listening:
                break
            if text:
                # Use root.after to safely update UI from a different thread
                self.root.after(0, self.update_display, text)

# --- PART 3: EXECUTION ---
if __name__ == "__main__":
    root = tk.Tk()
    app = SehatSathiApp(root)
    root.mainloop()