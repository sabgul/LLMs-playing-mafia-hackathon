from engine.players import get_initial_players, MODERATOR_CONFIG
from engine.llm_client import call_llm
from engine.players import Agent


def connectivity_test():
    agents = get_initial_players()

    # 1. Test a Player (Gemini)
    alice = agents[0]  # The Mafia
    print(f"Testing Agent {alice.id} ({alice.name} - {alice.role})...")

    res = call_llm(
        alice,
        f"You are {alice.role} in a high-stakes game. Deceive the others.",
        "The game just started. What is your first move?"
    )
    print(f"[prompt]: You are {alice.role} in a high-stakes game. Deceive the others.",
          "The game just started. What is your first move?")
    print(f"THOUGHT: {res['thought']}...")  # Secret intent
    print(f"PUBLIC: {res['public']}\n")

    # 2. Test the Moderator
    mod_agent = Agent(0, "GM", "Moderator", MODERATOR_CONFIG['model'], "groq")

    print(f"Testing Moderator (Groq)...")
    res_mod = call_llm(
        mod_agent,
        "You are the Game Master.",
        "Summarize this: Agent 1 says they are the Doctor. Agent 2 doesn't believe them."
    )
    print(f"[prompt]: You are the Game Master.",
          "Summarize this: Agent 1 says they are the Doctor. Agent 2 doesn't believe them.")
    print(f"MODERATOR: {res_mod['public']}")


if __name__ == "__main__":
    connectivity_test()
