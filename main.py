import os
import shutil
from datetime import datetime
from engine.players import get_initial_players, MODERATOR_CONFIG
from engine.game_state import MafiaGameState
from engine.llm_client import call_llm
from engine.logger import setup_live_folder, log_to_blackboard, log_to_dev
from engine.prompts import BASE_RULES, IDENTITY_STRINGS, PHASE_TASKS, MODERATOR_SUMMARY_PROMPT

LIVE_DIR = "live_session_output"
FINAL_DIR = "outputs"


def get_roster(game):
    living = game.get_living_agents()
    return "\n".join([f"- Agent {a.id}: {a.name}" for a in living])


def get_full_prompt(agent, game, task_key, world_summary, extra_data=None):
    # 1. Partner Logic for Mafia
    partner_name = "None"
    if agent.role == "Mafia":
        partner = next((a for a in game.agents if a.role == "Mafia" and a.id != agent.id), None)
        partner_name = partner.name if partner else "None"

    # 2. Identity String
    identity = IDENTITY_STRINGS[agent.role].format(
        name=agent.name,
        id=agent.id,
        partner=partner_name
    )

    # 3. Memory Block (The Amnesia Fix)
    memory_block = "\n### YOUR MEMORY (PAST TURNS) ###\n"
    if not agent.history:
        memory_block += "This is the start of the game. You have no past actions.\n"
    else:
        for entry in agent.history:
            memory_block += f"[Round {entry['round']}] You thought: {entry['thought']}\n"
            memory_block += f"[Round {entry['round']}] You said publicly: {entry['public']}\n"

    # 4. Final System Construction
    full_system = f"""
    {BASE_RULES}
    {identity}

    ### PUBLIC WORLD STATE (Moderator Summary) ###
    {world_summary}

    ### YOUR PRIVATE LOGS (Memory of your thoughts and actions) ###
    {memory_block}
    """

    # 5. Task Logic
    task = PHASE_TASKS[task_key]
    if extra_data:
        # This handles injecting things like {wave_1_statements}
        task = task.format(**extra_data)

    return full_system, task


def get_game_summary(blackboard_file_path):
    if not os.path.exists(blackboard_file_path):
        return "The game has just begun."

    with open(blackboard_file_path, 'r') as f:
        full_transcript = f.read()

    # Use Groq/Llama for speed and cost
    # We use a neutral "Moderator" persona here
    res = call_llm(MODERATOR_CONFIG, MODERATOR_SUMMARY_PROMPT, full_transcript)
    return res['public']


def run_game():
    agents = get_initial_players()
    game = MafiaGameState(agents)
    setup_live_folder(LIVE_DIR)

    manifest = "\n".join([
        f"Agent {a.id} ({a.name}): Model={a.model}, Provider={a.provider}, Role={a.role}"
        for a in agents
    ])
    log_to_dev(LIVE_DIR, f"SYSTEM: Game Manifest Initialized.\n{manifest}\n\nGAME START: Roles assigned.")

    try:
        while not game.game_over:
            roster = get_roster(game)
            log_to_dev(LIVE_DIR, f"--- ROUND {game.round_num} START ---")

            blackboard_path = os.path.join(LIVE_DIR, "blackboard.txt")
            world_summary = get_game_summary(blackboard_path)

            # ==========================
            # PHASE 1: NIGHT
            # ==========================
            log_to_dev(LIVE_DIR, "PHASE: Night")

            # Mafia Borda Kill
            mafia_responses = []
            mafiosos = [a for a in game.get_living_agents() if a.role == "Mafia"]
            for m in mafiosos:
                sys_p, task_p = get_full_prompt(m, game, "night_mafia", world_summary)
                user_p = f"CURRENT ROSTER:\n{roster}\n{task_p}"

                res = call_llm(m, sys_p, user_p)
                m.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num)
                mafia_responses.append(res['public'])

            # NEW: Name-based Borda resolution
            kill_id = game.resolve_borda_kill_by_name(mafia_responses)

            # Doctor Save
            doc = game.get_doctor_agent()
            save_id = None
            if doc:
                # Use the name-based last_saved for the prompt
                sys_p, task_p = get_full_prompt(doc, game, "night_doctor", world_summary, {"last_saved": game.last_saved_name})
                user_p = f"CURRENT ROSTER:\n{roster}\n{task_p}"

                res = call_llm(doc, sys_p, user_p)
                # doc.save_turn(LIVE_DIR, res['thought'], "[PRIVATE NIGHT ACTION]", game.round_num)
                doc.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num)
                # Helper to find the ID from the name mentioned
                save_name = res['public']
                living_agents = game.get_living_agents()
                # Find which living player's name is in the response
                matched_agent = next((a for a in living_agents if a.name.lower() in save_name.lower()), None)
                save_id = matched_agent.id if matched_agent else doc.id  # Default to self-save if hallucinated

            # Resolution
            report, victim = game.resolve_night(kill_id, save_id)
            log_to_blackboard(LIVE_DIR, "Moderator", report)

            if victim:
                log_to_dev(LIVE_DIR,
                           f"RESULT: Night {game.round_num} - {victim.name} (Agent {victim.id}) was KILLED. Role: {victim.role}")
            else:
                log_to_dev(LIVE_DIR, f"RESULT: Night {game.round_num} - No one died.")

            # if game.check_win(): break
            if game.check_win():
                living_final = [a.name for a in game.get_living_agents()]
                summary = f"******************************\nFINAL GAME RESULT: {game.winner.upper()} WIN\nTotal Rounds: {game.round_num}\nSurvivors: {living_final}\n******************************"
                log_to_dev(LIVE_DIR, summary)
                break

            # ==========================
            # PHASE 2: DAY (2-WAVE)
            # ==========================
            log_to_dev(LIVE_DIR, "PHASE: Day Discussion")

            # WAVE 1: Claims & Questions
            wave1_transcript = ""
            living_agents = game.get_living_agents()
            for a in living_agents:
                sys_p, task_p = get_full_prompt(a, game, "day_wave_1", world_summary)
                user_p = f"MODERATOR REPORT:\n{report}\nCURRENT ROSTER:\n{roster}\n{task_p}"

                res = call_llm(a, sys_p, user_p)
                a.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num)
                wave1_transcript += f"{a.name}: {res['public']}\n"

            # WAVE 2: Rebuttals
            for a in living_agents:
                # We pass the wave1_transcript into the format dict
                sys_p, task_p = get_full_prompt(a, game, "day_wave_2", world_summary, {"wave_1_statements": wave1_transcript})
                user_p = task_p  # The formatted task contains the statements

                res = call_llm(a, sys_p, user_p)
                a.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num)

            # ==========================
            # PHASE 3: VOTING
            # ==========================
            log_to_dev(LIVE_DIR, "PHASE: Voting")
            votes = []
            living_names = [a.name for a in living_agents]

            for a in living_agents:
                sys_p, _ = get_full_prompt(a, game, "vote", world_summary)
                user_p = f"FINAL VOTE: Who do you want to eliminate? State the NAME of the player. (Living: {', '.join(living_names)})"

                res = call_llm(a, sys_p, user_p)
                votes.append(res['public'])
                log_to_dev(LIVE_DIR, f"VOTE CAST: {a.name} voted. (Thought: {res['thought']})")

            v_report, v_victim = game.resolve_vote_by_name(votes)
            log_to_blackboard(LIVE_DIR, "Moderator", v_report)

            if v_victim:
                log_to_dev(LIVE_DIR,
                           f"RESULT: Day {game.round_num} - {v_victim.name} was EXECUTED. Role: {v_victim.role}")
            else:
                log_to_dev(LIVE_DIR, f"RESULT: Day {game.round_num} - No one was voted out.")

            if game.check_win():
                living_final = [a.name for a in game.get_living_agents()]
                summary = f"******************************\nFINAL GAME RESULT: {game.winner.upper()} WIN\nTotal Rounds: {game.round_num}\nSurvivors: {living_final}\n******************************"
                log_to_dev(LIVE_DIR, summary)
                break

            living_summary = ", ".join([f"{a.name}({a.id})" for a in game.get_living_agents()])
            log_to_dev(LIVE_DIR, f"STATUS: Round {game.round_num} End. Living: [{living_summary}]")
            game.round_num += 1

    except Exception as e:
        log_to_dev(LIVE_DIR, f"CRITICAL ERROR: {str(e)}")
        print(f"Error: {e}")

    finally:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_path = os.path.join(FINAL_DIR, f"game_{timestamp}")
        shutil.move(LIVE_DIR, final_path)
        print(f"Game finished. Results in {final_path}")


if __name__ == "__main__":
    run_game()