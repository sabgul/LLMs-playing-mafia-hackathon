import shutil
from datetime import datetime
import os

LIVE_DIR = "live_session_output"
FINAL_DIR = "outputs"


def run_game():
    try:
        # 1. Setup live folder
        if not os.path.exists(LIVE_DIR):
            os.makedirs(LIVE_DIR)

        # 2. RUN GAME LOGIC HERE...

    except Exception as e:
        print(f"Game crashed: {e}")

    finally:
        # 3. Archive the game
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join(FINAL_DIR, f"game_{timestamp}")
        shutil.move(LIVE_DIR, archive_path)
        print(f"Game archived to {archive_path}")


if __name__ == '__main__':
    print(f'Hi')
