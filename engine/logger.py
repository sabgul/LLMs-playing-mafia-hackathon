import os
from datetime import datetime


def setup_live_folder(directory="live_session_output"):
    """Ensures a clean slate for the current game."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Clear any old files from a previous crashed run
    for file in os.listdir(directory):
        os.remove(os.path.join(directory, file))


def append_to_file(directory, filename, content):
    """Generic helper to write with a timestamp."""
    path = os.path.join(directory, filename)
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(path, "a") as f:
        f.write(f"[{timestamp}] {content}\n")


def log_to_blackboard(directory, agent_name, message):
    """The public record that agents actually read."""
    content = f"{agent_name}: {message}\n"
    append_to_file(directory, "blackboard.txt", content)


def log_to_dev(directory, event):
    """The 'God View' for programmers only."""
    append_to_file(directory, "dev_log.txt", event)
