import os
import shutil
import random
import concurrent.futures
from datetime import datetime

from engine.game_state import MafiaGameState
from engine.llm_client import call_llm
from engine.logger import setup_live_folder, log_to_dev, log_to_blackboard
from engine.players import get_initial_players, get_moderator
from engine.prompts import PERSONAL_SUMMARY_PROMPT, MODERATOR_SUMMARY_PROMPT, PHASE_TASKS, IDENTITY_STRINGS, BASE_RULES, \
    BEHAVIOR_LEVELS
from engine.judge import run_analysis

LIVE_DIR = "live_session_output"
FINAL_DIR = "outputs"


# def run_experiment_suite():
#     levels = [1, 2, 3, 4]
#     trials = 5
#
#     for t in range(1, trials + 1):
#         for m_level in levels:
#             for d_level in levels:
#                 print(f"[Trial {t}/5] Mafia Lvl {m_level}, Doc Lvl {d_level}")
#
#                 result_name = run_game(mafia_level=m_level, doc_level=d_level)
#                 run_analysis(result_name)


def run_single_experiment(m_level, d_level, trial_num):
    """Worker function for one game."""
    print(f"🚀 Starting: [Trial {trial_num}] Mafia Lvl {m_level}, Doc Lvl {d_level}")
    try:
        # Run the game
        result_name = run_game(mafia_level=m_level, doc_level=d_level)
        # Run analysis (Judge) immediately after
        run_analysis(result_name)
        return f"✅ Finished: M{m_level} D{d_level} T{trial_num}"
    except Exception as e:
        return f"❌ Failed: M{m_level} D{d_level} T{trial_num} - Error: {e}"


def run_experiment_suite_parallel(max_workers=4):
    levels = [1, 2, 3, 4]
    trials = 3

    # Create a list of all tasks
    tasks = []
    for t in range(1, trials + 1):
        for m_lvl in levels:
            for d_lvl in levels:
                tasks.append((m_lvl, d_lvl, t))

    # Run them in parallel
    print(f"🔥 Parallelizing suite with {max_workers} workers...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # map handles the distribution of tasks
        futures = [executor.submit(run_single_experiment, m, d, t) for m, d, t in tasks]

        for future in concurrent.futures.as_completed(futures):
            print(future.result())


def run_game(mafia_level, doc_level):
    agents = get_initial_players()
    moderator = get_moderator()

    for a in agents:
        if a.role == "Mafia":
            a.behavior_level = mafia_level
        elif a.role == "Doctor":
            a.behavior_level = doc_level
        else:
            a.behavior_level = 2

    game = MafiaGameState(agents)
    setup_live_folder(LIVE_DIR)

    roster_details = "\n".join([
        f"Agent {a.id} ({a.name}): Model={a.model}, Provider={a.provider}, Role={a.role}"
        for a in agents
    ])

    manifest = f"""
    {roster_details}

    ### EXPERIMENT SETUP ###
    Behavior level setup: Mafia Level {mafia_level}, Doctor Level {doc_level}
    """

    log_to_dev(LIVE_DIR, f"SYSTEM: Game Manifest Initialized.\n{manifest}\n\nGAME START: Roles assigned.")

    try:
        while not game.game_over:
            roster = get_roster(game)
            log_to_dev(LIVE_DIR, f"--- ROUND {game.round_num} START ---")

            blackboard_path = os.path.join(LIVE_DIR, "blackboard.txt")
            world_summary = get_game_summary(moderator, blackboard_path)

            # ==========================
            # PHASE 1: NIGHT
            # ==========================
            log_to_dev(LIVE_DIR, "PHASE: Night")

            # Mafia Borda Kill
            mafia_responses = []
            mafiosos = [a for a in game.get_living_agents() if a.role == "Mafia"]
            for m in mafiosos:
                sys_p, task_p = get_full_prompt(m, moderator, game, "night_mafia", world_summary)
                user_p = f"CURRENT ROSTER:\n{roster}\n{task_p}"
                res = call_llm(m, sys_p, user_p)

                if "API ERROR" in res['public']:
                    print(f"🛑 API ERROR for {m.name} (Mafia) at Night. Using fallback.")
                    res['thought'] = "I am having trouble connecting to my strategic thoughts."
                    res['public'] = "[]"

                m.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num, broadcast=False)
                mafia_responses.append(res['public'])

            kill_id = game.resolve_borda_kill_by_name(mafia_responses)

            # Doctor Save
            doc = game.get_doctor_agent()
            save_id = None
            if doc:
                sys_p, task_p = get_full_prompt(doc, moderator, game, "night_doctor", world_summary, {"last_saved": game.last_saved_name})
                user_p = f"CURRENT ROSTER:\n{roster}\n{task_p}"

                res = call_llm(doc, sys_p, user_p)

                if "API ERROR" in res['public']:
                    print(f"🛑 API ERROR for {doc.name} (Doctor) at Night. Using fallback.")
                    res['thought'] = "I cannot determine who to save due to a mental block."
                    res['public'] = f"{doc.name}"

                doc.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num, broadcast=False)
                save_name = res['public']
                living_agents = game.get_living_agents()
                matched_agent = next((a for a in living_agents if a.name.lower() in save_name.lower()), None)
                save_id = matched_agent.id if matched_agent else doc.id  # Default to self-save if hallucinated

            report, victim = game.resolve_night(kill_id, save_id)
            log_to_blackboard(LIVE_DIR, "Moderator", report)

            if victim:
                log_to_dev(LIVE_DIR,
                           f"RESULT: Night {game.round_num} - {victim.name} (Agent {victim.id}) was KILLED. Role: {victim.role}")
            else:
                log_to_dev(LIVE_DIR, f"RESULT: Night {game.round_num} - No one died.")

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
                sys_p, task_p = get_full_prompt(a, moderator, game, "day_wave_1", world_summary)
                user_p = f"MODERATOR REPORT:\n{report}\nCURRENT ROSTER:\n{roster}\n{task_p}"

                res = call_llm(a, sys_p, user_p)
                if "API ERROR" in res['public']:
                    print(f"🛑 API ERROR for {a.name} during Day Wave 1.")
                    res['thought'] = "Connection lost. Cannot formulate argument."
                    res['public'] = "I am currently observing the situation and have no comment yet."
                a.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num)
                wave1_transcript += f"{a.name}: {res['public']}\n"

            # WAVE 2: Rebuttals
            for a in living_agents:
                # pass the wave1_transcript into the format dict
                sys_p, task_p = get_full_prompt(a, moderator, game, "day_wave_2", world_summary, {"wave_1_statements": wave1_transcript})
                user_p = task_p

                res = call_llm(a, sys_p, user_p)
                if "API ERROR" in res['public']:
                    print(f"🛑 API ERROR for {a.name} during Day Wave 2.")
                    res['thought'] = "Connection lost. Cannot rebuttal."
                    res['public'] = "I have nothing further to add to my previous statement."
                a.save_turn(LIVE_DIR, res['thought'], res['public'], game.round_num)

            # ==========================
            # PHASE 3: VOTING
            # ==========================
            log_to_dev(LIVE_DIR, "PHASE: Voting")
            votes = []
            living_names = [a.name for a in living_agents]

            for a in living_agents:
                sys_p, _ = get_full_prompt(a, moderator, game, "vote", world_summary)
                user_p = f"FINAL VOTE: Who do you want to eliminate? State the NAME of the player. (Living: {', '.join(living_names)})"

                res = call_llm(a, sys_p, user_p)
                if "API ERROR" in res['public']:
                    print(f"🛑 API ERROR for {a.name} during Voting.")
                    res['thought'] = "Connection lost. Voting randomly to maintain game flow."
                    # Random vote fallback to ensure the engine doesn't break
                    res['public'] = random.choice([name for name in living_names if name != a.name])

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
        return f"game_{timestamp}"


def get_roster(game):
    living = game.get_living_agents()
    return "\n".join([f"- Agent {a.id}: {a.name}" for a in living])


def get_full_prompt(agent, moderator, game, task_key, world_summary, extra_data=None):
    partner_name = "None"
    if agent.role == "Mafia":
        partner = next((a for a in game.agents if a.role == "Mafia" and a.id != agent.id), None)
        partner_name = partner.name if partner else "None"

    identity = IDENTITY_STRINGS[agent.role].format(
        name=agent.name,
        id=agent.id,
        partner=partner_name
    )
    behavior_instruction = BEHAVIOR_LEVELS.get(agent.behavior_level, "")
    personal_summary = get_scratchpad_summary(moderator, agent, LIVE_DIR)

    full_system = f"""
    {BASE_RULES}
    {identity}

    ### YOUR STRATEGIC BEHAVIORAL GUIDELINES ###
    {behavior_instruction}

    ### PUBLIC WORLD STATE (Moderator Summary) ###
    {world_summary}

    ### YOUR PRIVATE STRATEGY (Summarized from your scratchpad) ###
    {personal_summary}
    """

    task = PHASE_TASKS[task_key]
    if extra_data:
        # handles injecting things like {wave_1_statements}
        task = task.format(**extra_data)

    prompts_path = os.path.join(LIVE_DIR, "prompts.txt")
    with open(prompts_path, "a") as f:
        f.write(f"====================================================\n")
        f.write(f"AGENT: {agent.name} | ROUND: {game.round_num} | TASK: {task_key}\n")
        f.write(f"====================================================\n")
        f.write(f"SYSTEM PROMPT:\n{full_system}\n")
        f.write(f"USER TASK:\n{task}\n\n")

    return full_system, task


def get_game_summary(moderator, file_path):
    if not os.path.exists(file_path):
        return "The game has just begun."

    try:
        with open(file_path, 'r') as f:
            full_transcript = f.read()

        res = call_llm(moderator, MODERATOR_SUMMARY_PROMPT, full_transcript)
        content = res.get('public', "").lower()

        if "api error" in content or not content:
            raise ValueError(f"ERROR: {moderator.model} returned an invalid response: {content}")

        return res['public']

    except Exception as e:
        error_msg = f"MODERATOR ERROR: {str(e)}. Falling back to raw transcript."
        log_to_dev(LIVE_DIR, error_msg)
        return f"Full summary unavailable due to technical glitch."


def get_scratchpad_summary(moderator, agent, live_dir):
    file_path = os.path.join(live_dir, f"agent_{agent.id}_{agent.name}.txt")

    if not os.path.exists(file_path):
        return "You have no private history yet. This is the beginning of your mission."

    try:
        with open(file_path, 'r') as f:
            scratchpad_content = f.read()

        res = call_llm(moderator, PERSONAL_SUMMARY_PROMPT, scratchpad_content)

        content = res.get('public', "").lower()
        if "api error" in content or not content:
            raise ValueError("Moderator failed to summarize scratchpad.")

        return res['public']

    except Exception as e:
        log_to_dev(live_dir, f"MEMORY ERROR for {agent.name}: {str(e)}")
        return f"Recent notes from your scratchpad:\n...{scratchpad_content[-1000:]}"


if __name__ == "__main__":
    run_experiment_suite()
