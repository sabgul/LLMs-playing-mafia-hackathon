import os
from dataclasses import dataclass, field
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
    behavior_level: int = 2
    history: List[Dict] = field(default_factory=list)

    def add_to_memory(self, thought, public_statement, round_num):
        self.history.append({
            "round": round_num,
            "thought": thought,
            "public": public_statement
        })

    def save_turn(self, directory, thought, public_message, round_num, broadcast=True):
        """Records both the secret intent and the public action."""
        scratch_file = f"agent_{self.id}_scratchpad.txt"
        append_to_file(directory, scratch_file, f"ROUND {round_num} THOUGHT: {thought}")

        if broadcast:
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
    player_model = "gemini/gemini-2.5-flash-lite"

    return [
        Agent(1, "Alice", "Mafia", player_model, "google"),
        Agent(2, "Bob", "Mafia", player_model, "google"),
        Agent(3, "Chris", "Villager", player_model, "google"),
        Agent(4, "David", "Villager", player_model, "google"),
        Agent(5, "Ethan", "Villager", player_model, "google"),
        Agent(6, "Frank", "Doctor", player_model, "google"),
    ]


def get_moderator() -> Agent:
    return Agent(7, "Moderator", "Moderator", "groq/llama-3.3-70b-versatile", "groq")


# Moderator is treated separately as a 'utility' rather than a 'player'
MODERATOR_CONFIG = {
    "name": "Moderator",
    # "model": "groq/llama-3.3-70b-versatile",
    "model": "gemini/gemini-2.5-flash-lite",
    "provider": "groq"
}
