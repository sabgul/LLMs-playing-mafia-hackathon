# import shutil
# from datetime import datetime
# import os
#
# from engine.game_state import MafiaGameState
# from engine.llm_client import call_llm
# from engine.logger import setup_live_folder, log_to_blackboard
# from engine.parser import extract_rankings, extract_single_id
# from engine.players import get_initial_players
#
# LIVE_DIR = "live_session_output"
# FINAL_DIR = "outputs"
#
#
# # TODO instead of using the hardcoded text, use prompts from files
# def run_game():
#     try:
#         # 1. Setup live folder
#         if not os.path.exists(LIVE_DIR):
#             os.makedirs(LIVE_DIR)
#
#         agents = get_initial_players()
#         game = MafiaGameState(agents)
#         setup_live_folder("live_session_output")
#
#         while not game.game_over:
#             # --- NIGHT PHASE ---
#             # 1. Mafia Choose (Using Borda Count)
#             mafia_choices = []
#             for m in [a for a in game.get_living_agents() if a.role == "Mafia"]:
#                 res = call_llm(m, "You are Mafia.", "Rank 4 players to kill: [ID1, ID2...]")
#                 mafia_choices.append(extract_rankings(res['public']))
#
#             # (Simplified for now: take first choice of first mafia) # TODO extend to borda count
#             kill_id = mafia_choices[0][0] if mafia_choices else None
#
#             # 2. Doctor Choose
#             doc = next((a for a in game.get_living_agents() if a.role == "Doctor"), None)
#             save_id = None
#             if doc:
#                 res = call_llm(doc, "You are Doctor.", f"Save someone. Not {game.last_saved_id}")
#                 save_id = extract_single_id(res['public'])
#
#             # 3. Night Result
#             report, victim = game.resolve_night(kill_id, save_id)
#             log_to_blackboard("live_session_output", "Moderator", report)
#
#             if game.check_win(): break
#
#             # --- DAY PHASE (The 2-Wave Discussion) ---
#             # WAVE 1: Claims
#             wave1_text = ""
#             for a in game.get_living_agents():
#                 res = call_llm(a, f"You are {a.role}", "Wave 1: Claim, Question, Intent.")
#                 a.save_turn("live_session_output", res['thought'], res['public'], game.round_num)
#                 wave1_text += f"{a.name}: {res['public']}\n"
#
#             # WAVE 2: Rebuttals
#             for a in game.get_living_agents():
#                 res = call_llm(a, f"You are {a.role}", f"Respond to this: {wave1_text}")
#                 a.save_turn("live_session_output", res['thought'], res['public'], game.round_num)
#
#             # FINAL VOTE
#             votes = []
#             for a in game.get_living_agents():
#                 res = call_llm(a, "Vote ID only.", "Who do you vote out?")
#                 votes.append(extract_single_id(res['public']))
#
#             v_report, v_victim = game.resolve_vote(votes)
#             log_to_blackboard("live_session_output", "Moderator", v_report)
#
#             if game.check_win(): break
#             game.round_num += 1
#
#         print(f"Game Over! Winners: {game.winner}")
#
#         # 2. RUN GAME LOGIC HERE...
#         # Inside the Night Phase of main.py
#         # doc = game.get_doctor_agent()
#         # if doc:
#         #     restricted = f" (Note: You cannot save Agent {game.last_saved_id} again tonight)" if game.last_saved_id else ""
#         #     doc_prompt = f"Who do you save? Living: {game.get_living_agents()}{restricted}"
#         # while not game.game_over:
#         #     run_night_phase(game)
#         #     if game.check_win(): break  # Stop if Mafia won at night
#         #
#         #     run_day_phase(game)
#         #     # Wave 1: Statements
#         #     for a in game.get_living_agents():
#         #     # Prompt: "Make a claim, ask a question, state intent."
#         #
#         #     # Wave 2: Responses
#         #     for a in game.get_living_agents():
#         #     # Prompt: "Answer questions and defend yourself."
#         #     if game.check_win(): break  # Stop if Villagers won the vote
#
#         # while not game.game_over:
#         #     # 1. NIGHT PHASE
#         #     # (Mafia kill, Doctor save, etc.)
#         #
#         #     # 2. TRANSITION TO DAY
#         #     # Get the "Story so far" from the Moderator
#         #     current_summary = get_moderated_context(agents, MODERATOR_CONFIG, "live_session_output/blackboard.txt")
#         #
#         #     # 3. DAY PHASE (Wave 1) - statements. Make a claim, ask a question, state intent.
#         #     for agent in game.get_living_agents():
#         #         # We pass the 'current_summary' into the prompt here!
#         #         user_prompt = f"MODERATOR SUMMARY: {current_summary}\n\nYour turn: Make a claim and a question."
#         #         res = call_llm(agent, agent.role_prompt, user_prompt)
#         #         agent.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num)
#     #       # 4. DAY PHASE (Wave 2) - Responses. Answer questions and defend yourself.
#
#         # --- Inside main.py: The Day Phase ---
#
#         # WAVE 1: The Openers
#         # wave_1_history = ""
#         # for agent in game.get_living_agents():
#         #     # Prompt: Make a claim, ask a question, state vote intent
#         #     res = call_llm(agent, system_prompts[agent.role],
#         #                    f"Context: {current_summary}\nAction: Open the discussion.")
#         #
#         #     # Save to files
#         #     agent.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num)
#         #
#         #     # Track for Wave 2
#         #     wave_1_history += f"{agent.name}: {res['public']}\n"
#         #
#         # # WAVE 2: The Rebuttals
#         # for agent in game.get_living_agents():
#         #     # We feed the specific Wave 1 chat into the prompt
#         #     rebuttal_prompt = f"""
#         #     The following claims and questions were just made:
#         #     {wave_1_history}
#         #
#         #     Your Task:
#         #     1. Answer any questions directed at you.
#         #     2. Defend yourself if accused.
#         #     3. Finalize your vote intent.
#         #     """
#         #     res = call_llm(agent, system_prompts[agent.role], rebuttal_prompt)
#         #
#         #     # Save to files
#         #     agent.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num)
#
#     except Exception as e:
#         print(f"Game crashed: {e}")
#
#     finally:
#         # 3. Archive the game
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         archive_path = os.path.join(FINAL_DIR, f"game_{timestamp}")
#         shutil.move(LIVE_DIR, archive_path)
#         print(f"Game archived to {archive_path}")
#
#
# def get_roster_message(agents):
#     living_agents = [a for a in agents if a.is_alive]
#     roster = "\n".join([f"- Agent {a.id}: {a.name}" for a in living_agents])
#     return f"CURRENT LIVING PLAYERS:\n{roster}"
#
#
# if __name__ == '__main__':
#     print(f'Hi')
import os
import shutil
from datetime import datetime
from engine.players import get_initial_players, MODERATOR_CONFIG
from engine.game_state import MafiaGameState
from engine.llm_client import call_llm
from engine.parser import extract_single_id, extract_rankings
from engine.logger import setup_live_folder, log_to_blackboard, log_to_dev
from engine.rate_limiter import RateLimiter
import time

LIVE_DIR = "live_session_output"
FINAL_DIR = "outputs"


def get_roster(game):
    living = game.get_living_agents()
    return "\n".join([f"- Agent {a.id}: {a.name}" for a in living])


def run_game():
    # 1. INITIALIZE
    agents = get_initial_players()
    game = MafiaGameState(agents)
    setup_live_folder(LIVE_DIR)

    # log_to_dev(LIVE_DIR, "GAME START: Roles assigned.")
    manifest = "\n".join([
        f"Agent {a.id} ({a.name}): Model={a.model}, Provider={a.provider}, Role={a.role}"
        for a in agents
    ])
    log_to_dev(LIVE_DIR, f"SYSTEM: Game Manifest Initialized.\n{manifest}\n\nGAME START: Roles assigned.")

    try:
        while not game.game_over:
            roster = get_roster(game)
            log_to_dev(LIVE_DIR, f"--- ROUND {game.round_num} START ---")

            # ==========================
            # PHASE 1: NIGHT
            # ==========================
            log_to_dev(LIVE_DIR, "PHASE: Night")

            # Mafia Borda Kill
            mafia_rankings = []
            mafiosos = [a for a in game.get_living_agents() if a.role == "Mafia"]
            for m in mafiosos:
                partner = next((a.name for a in mafiosos if a.id != m.id), "None")
                prompt = f"ROSTER:\n{roster}\nPartner: {partner}. Rank 4 players to kill (e.g. [4, 2, 1, 5])."
                res = call_llm(m, f"You are Mafia. Partner: {partner}", prompt)
                m.save_turn(LIVE_DIR, res['thought'], "[PRIVATE NIGHT ACTION]", game.round_num)
                mafia_rankings.append(extract_rankings(res['public']))

            kill_id = game.resolve_borda_kill(mafia_rankings)

            # Doctor Save
            doc = game.get_doctor_agent()
            save_id = None
            if doc:
                restricted = f" (Cannot save {game.last_saved_id})" if game.last_saved_id else ""
                prompt = f"ROSTER:\n{roster}\nWho do you save?{restricted}"
                res = call_llm(doc, "You are the Doctor.", prompt)
                doc.save_turn(LIVE_DIR, res['thought'], "[PRIVATE NIGHT ACTION]", game.round_num)
                save_id = extract_single_id(res['public'])

            # Resolution
            report, victim = game.resolve_night(kill_id, save_id)
            log_to_blackboard(LIVE_DIR, "Moderator", report)
            # log_to_dev(LIVE_DIR, f"Logic: Mafia targeted {kill_id}, Doctor saved {save_id}")
            if victim:
                log_to_dev(LIVE_DIR,
                           f"RESULT: Night {game.round_num} - {victim.name} (Agent {victim.id}) was KILLED. Role: {victim.role}")
            else:
                log_to_dev(LIVE_DIR, f"RESULT: Night {game.round_num} - No one died (Doctor saved Agent {save_id})")

            if game.check_win(): break

            # ==========================
            # PHASE 2: DAY (2-WAVE)
            # ==========================
            log_to_dev(LIVE_DIR, "PHASE: Day Discussion")

            # WAVE 1: Claims & Questions
            wave1_transcript = ""
            for a in game.get_living_agents():
                prompt = f"ROSTER:\n{roster}\n{report}\nAction: 1. Claim/Suspicion 2. Question 3. Vote Intent."
                res = call_llm(a, f"You are {a.role}.", prompt)
                a.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num)
                wave1_transcript += f"{a.name}: {res['public']}\n"

            # WAVE 2: Rebuttals
            for a in game.get_living_agents():
                prompt = f"WAVE 1 DISCUSSION:\n{wave1_transcript}\nAction: Respond to questions/accusations and finalize intent."
                res = call_llm(a, f"You are {a.role}.", prompt)
                a.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num)

            # FINAL VOTE
            # log_to_dev(LIVE_DIR, "PHASE: Voting")
            # votes = []
            # for a in game.get_living_agents():
            #     res = call_llm(a, f"You are {a.role}.", "Who do you vote out? Respond ONLY with ID.")
            #     vote_id = extract_single_id(res['public'])
            #     if vote_id: votes.append(vote_id)
            #
            # v_report, v_victim = game.resolve_vote(votes)
            # log_to_blackboard(LIVE_DIR, "Moderator", v_report)
            # if v_victim:
            #     log_to_dev(LIVE_DIR,
            #                f"RESULT: Day {game.round_num} - {v_victim.name} (Agent {v_victim.id}) was EXECUTED. Role: {v_victim.role}")
            # else:
            #     log_to_dev(LIVE_DIR, f"RESULT: Day {game.round_num} - No one was voted out.")
            # FINAL VOTE
            log_to_dev(LIVE_DIR, "PHASE: Voting")
            votes = []

            # Get a list of names currently in the game for validation
            living_names = [a.name for a in game.get_living_agents()]

            for a in game.get_living_agents():
                # 1. Update the prompt to ask for a NAME
                res = call_llm(a, get_full_system_prompt(a, game.agents),
                               f"FINAL VOTE: Who do you want to eliminate? State the NAME of the player. (Living: {', '.join(living_names)})")

                # 2. We save the text response (The LLM might say "I vote for Alice" or just "Alice")
                votes.append(res['public'])

                # Log their private thought about why they are voting this way
                log_to_dev(LIVE_DIR, f"VOTE CAST: {a.name} voted based on thought: {res['thought']}")

            # 3. Use the new name-based resolver in game_state
            v_report, v_victim = game.resolve_vote_by_name(votes)

            # 4. Standard reporting
            log_to_blackboard(LIVE_DIR, "Moderator", v_report)

            if v_victim:
                log_to_dev(LIVE_DIR,
                           f"RESULT: Day {game.round_num} - {v_victim.name} was EXECUTED. Role: {v_victim.role}")
            else:
                log_to_dev(LIVE_DIR, f"RESULT: Day {game.round_num} - No one was voted out.")


            # if game.check_win(): break
            if game.check_win():
                living_names = [a.name for a in game.get_living_agents()]
                summary = f"""******************************\n
                FINAL GAME RESULT: {game.winner.upper()} WIN\n
                Total Rounds: {game.round_num}\n
                Survivors: {living_names}\n
                ******************************"""
                log_to_dev(LIVE_DIR, summary)
                break
            living_summary = ", ".join([f"{a.name}({a.id})" for a in game.get_living_agents()])
            log_to_dev(LIVE_DIR, f"STATUS: Round {game.round_num} End. Living: [{living_summary}]")
            game.round_num += 1

    except Exception as e:
        log_to_dev(LIVE_DIR, f"CRITICAL ERROR: {str(e)}")
        print(f"Error: {e}")

    finally:
        # ARCHIVE
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_path = os.path.join(FINAL_DIR, f"game_{timestamp}")
        shutil.move(LIVE_DIR, final_path)
        print(f"Game finished. Results in {final_path}")


if __name__ == "__main__":
    run_game()
