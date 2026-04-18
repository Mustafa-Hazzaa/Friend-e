import threading

from STT import STT
from wake_word import listen_for_wake_word


class STTPipeline:
    def __init__(self, text):
        self.stt = STT(text=text)

    def start(self):
        self.stt.start_stream()
        threading.Thread(
            target=listen_for_wake_word,
            args=(self.stt.arm,),
            daemon=True
        ).start()

    def stop(self):
        self.stt.stop()