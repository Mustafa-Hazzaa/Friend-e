import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import webrtcvad


class STT():
    SAMPLE_RATE = 16000
    BLOCK_SIZE = 480   # 30ms at 16kHz
    MODEL_SIZE = "medium.en"

    def __init__(self):
        self.vad = webrtcvad.Vad(2)
        self.model = WhisperModel(self.MODEL_SIZE, device="cpu", compute_type="int8")

        self.stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            blocksize=self.BLOCK_SIZE,
            dtype='int16',
            callback=self.audio_callback
        )

        self.listening = True
        self.recording = False
        self.audio_buffer = []
        self.silence_counter = 0

    def start_listening(self):
        self.stream.start()
        while True:
            sd.sleep(100)

    def audio_callback(self, indata, frames, time_info, status):
s

    def model_transcribe(self, audio) -> str:
        print("🎙️ whisper is working...")
        segments, _ = self.model.transcribe(audio, beam_size=5) #higher beam_size more accurate but slower
        text = " ".join(segment.text for segment in segments)
        print(f"🧠 Transcription Result: {text}")
        return text