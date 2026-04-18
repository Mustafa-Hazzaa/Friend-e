from wake_word import listen_for_wake_word
from STT import STT


def on_wake():
    stt = STT()
    stt.start()



if __name__ == "__main__":
    listen_for_wake_word(on_wake)