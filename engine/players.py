from dataclasses import dataclass, field
import os

from engine.logger import append_to_file, log_to_blackboard
from typing import List, Dict


@dataclass
class Agent:
    id: int
    name: str
    role: str
    model: str
    provider: str
    is_alive: bool = True
    history: List[Dict] = field(default_factory=list)

    def add_to_memory(self, thought, public_statement, round_num):
        self.history.append({
            "round": round_num,
            "thought": thought,
            "public": public_statement
        })

    def save_turn(self, directory, thought, public_message, round_num):
        """Records both the secret intent and the public action."""
        # 1. Save the Scratchpad (Intent)
        scratch_file = f"agent_{self.id}_scratchpad.txt"
        append_to_file(directory, scratch_file, f"ROUND {round_num} THOUGHT: {thought}")

        # 2. Update the Blackboard (The Action)
        log_to_blackboard(directory, self.name, public_message)

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
    # player_model = "gemini/gemini-2.5-flash"
    player_model = "gemini/gemini-2.5-flash-lite"
    # player_model = "gemini/gemini-2.5-flash"

    return [
        Agent(1, "Alice", "Mafia", player_model, "google"),
        # Agent(2, "Bob", "Mafia", "groq/llama-3.3-70b-versatile", "groq"),  # Switched
        # Agent(3, "Chris", "Villager", "groq/llama-3.3-70b-versatile", "groq"),  # Switched
        Agent(2, "Bob", "Mafia", player_model, "google"),
        Agent(3, "Chris", "Villager", player_model, "google"),
        Agent(4, "David", "Villager", player_model, "google"),
        Agent(5, "Ethan", "Villager", player_model, "google"),
        Agent(6, "Frank", "Doctor", player_model, "google"),
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
