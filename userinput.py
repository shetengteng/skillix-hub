import time
import os

PROMPT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts.txt")

def wait_for_input():
    last_content = ""
    try:
        with open(PROMPT_FILE, "r") as f:
            last_content = f.read().strip()
    except FileNotFoundError:
        pass

    if last_content:
        print(last_content)
        with open(PROMPT_FILE, "w") as f:
            f.write("")
        return

    print("Waiting for user input in prompts.txt...")
    while True:
        try:
            with open(PROMPT_FILE, "r") as f:
                content = f.read().strip()
            if content and content != last_content:
                print(content)
                with open(PROMPT_FILE, "w") as f:
                    f.write("")
                return
        except FileNotFoundError:
            pass
        time.sleep(1)

if __name__ == "__main__":
    wait_for_input()
