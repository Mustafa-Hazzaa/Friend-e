import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import webrtcvad
import queue
import threading


class STT:
    def __init__(self, on_text):
        self.on_text = on_text
        self._armed = False
        self.vad = webrtcvad.Vad(3)
        self.model = WhisperModel(self.MODEL_SIZE, device="cpu", compute_type="int8")
        self.audio_queue = queue.Queue()

        self._audio_buffer = []
        self._silence_counter = 0.0
        self._stream = sd.InputStream( samplerate=self.SAMPLE_RATE,channels=1,blocksize=self.BLOCK_SIZE,dtype='int16',callback=self._audio_callback
        )

    def start_stream(self):
        threading.Thread(target=self._transcription_worker, daemon=True).start()
        self._stream.start()

    def arm(self):
        self._armed = True
        self._audio_buffer = []
        self._silence_counter = 0.0
        print("[STT] Listening...")

    def _audio_callback(self, indata):
        if not self._armed:
            return

        audio = indata[:, 0]
        speaking = self.vad.is_speech(audio.tobytes(), self.SAMPLE_RATE)
        self._audio_buffer.append(audio.copy())

        if speaking:
            self._silence_counter = 0.0
        else:
            self._silence_counter += self.BLOCK_SIZE / self.SAMPLE_RATE

        if self._silence_counter >= self.SILENCE_DURATION:
            if len(self._audio_buffer) > 10:
                audio_array = np.concatenate(self._audio_buffer).astype(np.float32) / 32768.0
                self.audio_queue.put(audio_array)
            self._armed = False
            print("STT Done ,waiting wake word...")

    def _transcription_worker(self):
        while True:
            audio = self.audio_queue.get()
            segments, _ = self.model.transcribe(audio, language="ar", no_speech_threshold=0.8, beam_size=5)
            text = " ".join(seg.text for seg in segments).strip()
            if text:
                self.on_text(text)

    def stop(self):
        self._stream.stop()