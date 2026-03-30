"""
Parallel experiment runner for LLM-Mafia.
Drop this file next to your existing main.py.

Usage:
  # Test with 1 game first
  python main_parallel.py --trials 1 --workers 1 --mafia-level 1 --doc-level 1

  # Full run: 16 configs × 10 trials = 160 games, 3 at a time
  python main_parallel.py --trials 10 --workers 3

  # Only specific configs
  python main_parallel.py --trials 10 --workers 3 --mafia-level 1 4 --doc-level 1 4

  # Resume if interrupted (skips configs that already have enough trials)
  python main_parallel.py --trials 10 --workers 3 --resume

After all games finish, run:  python batch_judge.py
"""

import os
import shutil
import argparse
import random
import glob
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

from engine.game_state import MafiaGameState
from engine.llm_client import call_llm
from engine.logger import setup_live_folder, log_to_dev, log_to_blackboard
from engine.players import get_initial_players, get_moderator
from engine.prompts import (
    PERSONAL_SUMMARY_PROMPT, MODERATOR_SUMMARY_PROMPT,
    PHASE_TASKS, IDENTITY_STRINGS, BASE_RULES, BEHAVIOR_LEVELS
)

FINAL_DIR = "outputs"


def run_single_game(mafia_level, doc_level, trial_num):
    """
    Run one complete Mafia game in its own process.
    Each game gets an isolated working directory so nothing conflicts.
    Returns the name of the output folder.
    """
    game_id = f"m{mafia_level}_d{doc_level}_t{trial_num}"
    live_dir = f"live_session_{game_id}_{os.getpid()}"

    try:
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
        setup_live_folder(live_dir)

        roster_details = "\n".join([
            f"Agent {a.id} ({a.name}): Model={a.model}, Provider={a.provider}, Role={a.role}"
            for a in agents
        ])
        manifest = f"""
        {roster_details}

        ### EXPERIMENT SETUP ###
        Behavior level setup: Mafia Level {mafia_level}, Doctor Level {doc_level}
        Trial: {trial_num}
        Game ID: {game_id}
        """
        log_to_dev(live_dir, f"SYSTEM: Game Manifest Initialized.\n{manifest}\n\nGAME START: Roles assigned.")

        while not game.game_over:
            roster = _get_roster(game)
            log_to_dev(live_dir, f"--- ROUND {game.round_num} START ---")

            blackboard_path = os.path.join(live_dir, "blackboard.txt")
            world_summary = _get_game_summary(moderator, blackboard_path, live_dir)

            # ==================
            # NIGHT PHASE
            # ==================
            log_to_dev(live_dir, "PHASE: Night")

            mafia_responses = []
            mafiosos = [a for a in game.get_living_agents() if a.role == "Mafia"]
            for m in mafiosos:
                sys_p, task_p = _get_full_prompt(m, moderator, game, "night_mafia", world_summary, live_dir)
                user_p = f"CURRENT ROSTER:\n{roster}\n{task_p}"
                res = call_llm(m, sys_p, user_p)
                if "API ERROR" in res['public']:
                    res['thought'] = "I am having trouble connecting to my strategic thoughts."
                    res['public'] = "[]"
                m.save_turn(live_dir, res['thought'], res['public'], game.round_num, broadcast=False)
                mafia_responses.append(res['public'])

            kill_id = game.resolve_borda_kill_by_name(mafia_responses)

            doc = game.get_doctor_agent()
            save_id = None
            if doc:
                sys_p, task_p = _get_full_prompt(
                    doc, moderator, game, "night_doctor", world_summary, live_dir,
                    {"last_saved": game.last_saved_name}
                )
                user_p = f"CURRENT ROSTER:\n{roster}\n{task_p}"
                res = call_llm(doc, sys_p, user_p)
                if "API ERROR" in res['public']:
                    res['thought'] = "I cannot determine who to save due to a mental block."
                    res['public'] = f"{doc.name}"
                doc.save_turn(live_dir, res['thought'], res['public'], game.round_num, broadcast=False)
                save_name = res['public']
                living_agents = game.get_living_agents()
                matched = next((a for a in living_agents if a.name.lower() in save_name.lower()), None)
                save_id = matched.id if matched else doc.id

            report, victim = game.resolve_night(kill_id, save_id)
            log_to_blackboard(live_dir, "Moderator", report)

            if victim:
                log_to_dev(live_dir, f"RESULT: Night {game.round_num} - {victim.name} was KILLED. Role: {victim.role}")
            else:
                log_to_dev(live_dir, f"RESULT: Night {game.round_num} - No one died.")

            if game.check_win():
                _log_final(game, live_dir)
                break

            # ==================
            # DAY PHASE
            # ==================
            log_to_dev(live_dir, "PHASE: Day Discussion")
            living_agents = game.get_living_agents()

            # Wave 1
            wave1_transcript = ""
            for a in living_agents:
                sys_p, task_p = _get_full_prompt(a, moderator, game, "day_wave_1", world_summary, live_dir)
                user_p = f"MODERATOR REPORT:\n{report}\nCURRENT ROSTER:\n{roster}\n{task_p}"
                res = call_llm(a, sys_p, user_p)
                if "API ERROR" in res['public']:
                    res['thought'] = "Connection lost. Cannot formulate argument."
                    res['public'] = "I am currently observing the situation and have no comment yet."
                a.save_turn(live_dir, res['thought'], res['public'], game.round_num)
                wave1_transcript += f"{a.name}: {res['public']}\n"

            # Wave 2
            for a in living_agents:
                sys_p, task_p = _get_full_prompt(
                    a, moderator, game, "day_wave_2", world_summary, live_dir,
                    {"wave_1_statements": wave1_transcript}
                )
                user_p = task_p
                res = call_llm(a, sys_p, user_p)
                if "API ERROR" in res['public']:
                    res['thought'] = "Connection lost. Cannot rebuttal."
                    res['public'] = "I have nothing further to add to my previous statement."
                a.save_turn(live_dir, res['thought'], res['public'], game.round_num)

            # ==================
            # VOTING
            # ==================
            log_to_dev(live_dir, "PHASE: Voting")
            votes = []
            living_names = [a.name for a in living_agents]

            for a in living_agents:
                sys_p, _ = _get_full_prompt(a, moderator, game, "vote", world_summary, live_dir)
                user_p = f"FINAL VOTE: Who do you want to eliminate? (Living: {', '.join(living_names)})"
                res = call_llm(a, sys_p, user_p)
                if "API ERROR" in res['public']:
                    res['thought'] = "Connection lost. Voting randomly."
                    res['public'] = random.choice([n for n in living_names if n != a.name])
                votes.append(res['public'])
                log_to_dev(live_dir, f"VOTE CAST: {a.name} voted. (Thought: {res['thought']})")

            v_report, v_victim = game.resolve_vote_by_name(votes)
            log_to_blackboard(live_dir, "Moderator", v_report)

            if v_victim:
                log_to_dev(live_dir, f"RESULT: Day {game.round_num} - {v_victim.name} was EXECUTED. Role: {v_victim.role}")

            if game.check_win():
                _log_final(game, live_dir)
                break

            game.round_num += 1

    except Exception as e:
        log_to_dev(live_dir, f"CRITICAL ERROR: {str(e)}")
        print(f"[{game_id}] Error: {e}")

    finally:
        os.makedirs(FINAL_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_name = f"game_m{mafia_level}_d{doc_level}_t{trial_num}_{timestamp}"
        final_path = os.path.join(FINAL_DIR, final_name)

        if os.path.exists(live_dir):
            shutil.move(live_dir, final_path)

        print(f"[{game_id}] Done -> {final_path}")
        return final_name


# === Helpers (same logic as your main.py, but take live_dir as parameter) ===

def _get_roster(game):
    return "\n".join([f"- Agent {a.id}: {a.name}" for a in game.get_living_agents()])


def _log_final(game, live_dir):
    living_final = [a.name for a in game.get_living_agents()]
    summary = (
        f"******************************\n"
        f"FINAL GAME RESULT: {game.winner.upper()} WIN\n"
        f"Total Rounds: {game.round_num}\n"
        f"Survivors: {living_final}\n"
        f"******************************"
    )
    log_to_dev(live_dir, summary)


def _get_full_prompt(agent, moderator, game, task_key, world_summary, live_dir, extra_data=None):
    partner_name = "None"
    if agent.role == "Mafia":
        partner = next((a for a in game.agents if a.role == "Mafia" and a.id != agent.id), None)
        partner_name = partner.name if partner else "None"

    identity = IDENTITY_STRINGS[agent.role].format(name=agent.name, id=agent.id, partner=partner_name)
    behavior_instruction = BEHAVIOR_LEVELS.get(agent.behavior_level, "")
    personal_summary = _get_scratchpad_summary(moderator, agent, live_dir)

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
        task = task.format(**extra_data)

    prompts_path = os.path.join(live_dir, "prompts.txt")
    with open(prompts_path, "a") as f:
        f.write(f"====================================================\n")
        f.write(f"AGENT: {agent.name} | ROUND: {game.round_num} | TASK: {task_key}\n")
        f.write(f"====================================================\n")
        f.write(f"SYSTEM PROMPT:\n{full_system}\n")
        f.write(f"USER TASK:\n{task}\n\n")

    return full_system, task


def _get_game_summary(moderator, file_path, live_dir):
    if not os.path.exists(file_path):
        return "The game has just begun."
    try:
        with open(file_path, 'r') as f:
            full_transcript = f.read()
        res = call_llm(moderator, MODERATOR_SUMMARY_PROMPT, full_transcript)
        content = res.get('public', "").lower()
        if "api error" in content or not content:
            raise ValueError(f"ERROR: {moderator.model} returned invalid response: {content}")
        return res['public']
    except Exception as e:
        log_to_dev(live_dir, f"MODERATOR ERROR: {str(e)}. Falling back.")
        return "Full summary unavailable due to technical glitch."


def _get_scratchpad_summary(moderator, agent, live_dir):
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


def count_existing_trials(mafia_level, doc_level):
    """Count completed trials for a config by checking output folders."""
    pattern = os.path.join(FINAL_DIR, f"game_m{mafia_level}_d{doc_level}_t*")
    return len(glob.glob(pattern))


def run_parallel_suite(trials, workers, mafia_levels=None, doc_levels=None, resume=False):
    m_levels = mafia_levels or [1, 2, 3, 4]
    d_levels = doc_levels or [1, 2, 3, 4]

    jobs = []
    for m in m_levels:
        for d in d_levels:
            existing = count_existing_trials(m, d) if resume else 0
            for t in range(existing + 1, trials + 1):
                jobs.append((m, d, t))

    if not jobs:
        print("Nothing to run — all trials already completed!")
        return

    total = len(jobs)
    print(f"\n{'='*60}")
    print(f"  PARALLEL MAFIA EXPERIMENT")
    print(f"  Total games to run: {total}")
    print(f"  Concurrent workers: {workers}")
    print(f"  Configs: {len(m_levels)*len(d_levels)} | Trials each: {trials}")
    if resume:
        print(f"  Mode: RESUME (skipping completed trials)")
    print(f"{'='*60}\n")

    completed = 0
    failed = 0

    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_job = {
            executor.submit(run_single_game, m, d, t): (m, d, t)
            for m, d, t in jobs
        }

        for future in as_completed(future_to_job):
            m, d, t = future_to_job[future]
            try:
                result_name = future.result()
                completed += 1
                print(f"  [{completed}/{total}] m{m}_d{d}_t{t} -> {result_name}")
            except Exception as e:
                failed += 1
                print(f"  [{completed+failed}/{total}] m{m}_d{d}_t{t} FAILED: {e}")

    print(f"\n{'='*60}")
    print(f"  DONE: {completed} succeeded, {failed} failed")
    print(f"  Now run:  python batch_judge.py")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parallel LLM-Mafia Experiment Runner")
    parser.add_argument("--trials", type=int, default=10, help="Trials per config (default: 10)")
    parser.add_argument("--workers", type=int, default=3, help="Concurrent games (default: 3)")
    parser.add_argument("--mafia-level", type=int, nargs="+", help="Mafia levels to run (default: 1 2 3 4)")
    parser.add_argument("--doc-level", type=int, nargs="+", help="Doctor levels to run (default: 1 2 3 4)")
    parser.add_argument("--resume", action="store_true", help="Skip configs with enough completed trials")
    args = parser.parse_args()

    run_parallel_suite(
        trials=args.trials,
        workers=args.workers,
        mafia_levels=args.mafia_level,
        doc_levels=args.doc_level,
        resume=args.resume,
    )