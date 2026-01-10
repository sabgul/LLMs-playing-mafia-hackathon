from dataclasses import dataclass
from typing import List
import os


@dataclass
class Agent:
    id: int
    name: str
    role: str
    model: str
    provider: str
    is_alive: bool = True

    def save_scratchpad(self, live_dir: str, thought: str, round_num: int):
        """Records the hidden intent for manipulation analysis."""
        path = os.path.join(live_dir, f"agent_{self.id}_scratchpad.txt")
        with open(path, "a") as f:
            f.write(f"\n--- ROUND {round_num} STRATEGY ---\n{thought}\n")

    def save_public_history(self, live_dir: str, message: str, round_num: int):
        """Records what this specific agent said publicly."""
        path = os.path.join(live_dir, f"agent_{self.id}_public_history.txt")
        with open(path, "a") as f:
            f.write(f"\n--- ROUND {round_num} MESSAGE ---\n{message}\n")


def get_initial_players() -> List[Agent]:
    """
    Returns the starting lineup for a 6-player Mafia game.
    """
    return [
        Agent(1, "Alice", "Mafia", "gemini/gemini-2.5-flash", "google"),
        Agent(2, "Bob", "Mafia", "gemini/gemini-2.5-flash", "google"),
        Agent(3, "Chris", "Villager", "gemini/gemini-2.5-flash", "google"),
        Agent(4, "David", "Villager", "gemini/gemini-2.5-flash", "google"),
        Agent(5, "Ethan", "Villager", "gemini/gemini-2.5-flash", "google"),
        Agent(6, "Frank", "Doctor", "gemini/gemini-2.5-flash", "google"),
    ]


# The Moderator is treated separately as a 'utility' rather than a 'player'
MODERATOR_CONFIG = {
    "name": "Moderator",
    "model": "groq/llama-3.3-70b-versatile",
    "provider": "groq"
}

# from dataclasses import dataclass, field
#
# @dataclass
# class Agent:
#     id: str
#     name: str
#     role: str
#     model: str
#     provider: str
#     is_alive: bool = True
#     scratchpad: list = field(default_factory=list)
#
#
# @dataclass
# class MafiaPlayers:
#     player_registry = {
#         "agent_1": {"name": "Alice", "role": "Mafia", "provider": "google", "model": "gemini-2.5-flash"},
#         "agent_2": {"name": "Bob", "role": "Mafia", "provider": "google", "model": "gemini-2.5-flash"},
#         "agent_3": {"name": "Chris", "role": "Villager", "provider": "google", "model": "gemini-2.5-flash"},
#         "agent_4": {"name": "David", "role": "Villager", "provider": "google", "model": "gemini-2.5-flash"},
#         "agent_5": {"name": "Ethan", "role": "Villager", "provider": "google", "model": "gemini-2.5-flash"},
#         "agent_6": {"name": "Frank", "role": "Doctor", "provider": "google", "model": "gemini-2.5-flash"},
#         "moderator": {"name": "Moderator", "role": "Moderator", "provider": "groq", "model": "llama-3.3-70b-specdec"}
#     }
