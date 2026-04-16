from wake_word import listen_for_wake_word


def on_wake():
    print("[Wall-E]")


if __name__ == "__main__":
    listen_for_wake_word(on_wake)