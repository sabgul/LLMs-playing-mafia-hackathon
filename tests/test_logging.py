import os
from engine.logger import setup_live_folder, log_to_blackboard, log_to_dev
from engine.llm_client import call_llm
from engine.players import get_initial_players


def run_scaffolding_test():
    # 1. Initialize
    LIVE_DIR = "test_live_session_output"
    setup_live_folder(LIVE_DIR)
    agents = get_initial_players()

    log_to_dev(LIVE_DIR, "SYSTEM: Starting 2-round Scaffolding Test.")
    log_to_blackboard(LIVE_DIR, "Moderator", "Morning breaks! Round 1 starts now.")

    # ROUND 1: Initial Claims
    print("--- ROUND 1: Claims ---")
    for agent in agents[:3]:
        res = call_llm(agent, f"You are {agent.role}.", "Wave 1: Make an initial claim.")
        agent.save_turn(LIVE_DIR, res['thought'], res['public'], 1)
        print(f"Logged Agent {agent.id} Wave 1.")

    # ROUND 2: Responses (Reading from the blackboard)
    print("\n--- ROUND 2: Responses ---")
    with open(os.path.join(LIVE_DIR, "blackboard.txt"), "r") as f:
        current_chat = f.read()

    for agent in agents[:3]:
        res = call_llm(agent, f"You are {agent.role}.", f"Current Chat: {current_chat}\nWave 2: Respond to others.")
        agent.save_turn(LIVE_DIR, res['thought'], res['public'], 2)
        print(f"Logged Agent {agent.id} Wave 2.")

    print("\nTest Complete. Check the 'live_session_output' folder!")


if __name__ == "__main__":
    run_scaffolding_test()
