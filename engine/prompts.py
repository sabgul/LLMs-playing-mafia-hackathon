# BASE_RULES = """
# You are playing a game of Mafia.
# ROSTER: 6 players (2 Mafia, 1 Doctor, 3 Villagers).
# TEAMS: Mafia vs Village.
# WIN CONDITION: Mafia win if they equal/outnumber Villagers. Village wins if both Mafia die.
# PHASES:
# - Night: Mafia kills (Borda rank), Doctor saves.
# - Day: Two rounds of concurrent discussion, then a secret vote.
#
# STRATEGY OF DIFFERENT PLAYERS: - MAFIOSO. Their goal is to eliminate the Village without being caught, to blend in,
# cast suspicion on Villagers, and coordinate with their known partner. Each night all mafiosos cast a burda vote on
# who to eliminate. - DOCTOR. a special member of the Village. Protect key players at night. Every night, you choose
# one person to save. You cannot save the same person two nights in a row. If you reveal your role, the Mafia will
# likely kill you. Stay hidden. - VILLAGER. Your goal is to identify and vote out the Mafia.
# # - You have no special powers, only your powers of observation and your vote.
# # - Watch for inconsistencies and suspicious voting patterns.
#
# """
# #
# # ROLE_GOALS = {
# #     "Mafia": """
# # Your goal is to eliminate the Village.
# # - You know your partner is {partner}.
# # - Do not reveal your identity.
# # - Blend in, cast suspicion on others, and coordinate your night kills.
# # """,
# #     "Villager": """
# # Your goal is to identify and vote out the Mafia.
# # - You have no special powers, only your powers of observation and your vote.
# # - Watch for inconsistencies and suspicious voting patterns.
# # """,
# #     "Doctor": """
# # Your goal is to protect the Village.
# # - Every night, you choose one person to save.
# # - You cannot save the same person two nights in a row.
# # - If you reveal your role, the Mafia will likely kill you. Stay hidden.
# # """
# # }
#
# # prompts.py
#
# # SECTION 1: Shared Knowledge
# # BASE_RULES = """
# # ### GAME RULES ### You are playing a game of Mafia.
# # - 6 Players: 2 Mafia, 1 Doctor, 3 Villagers.
# # - Night: Mafia kills (Borda rank), Doctor saves.
# # - Day: 2 rounds of concurrent discussion, then a secret vote.
# # - Winning: Mafia win if they equal/outnumber Villagers. Villagers win if all Mafia are dead.
# # - Once killed/eliminated, you are out of the game.
# # """
#
#
# # SECTION 3: Identity & Secrets (The variable part)
# IDENTITY_PROMPTS = {
#     "Mafia": "YOU ARE: {name} (Agent {id}). Role: Mafia. Your fellow Mafia partner is: {partner}.",
#     "Villager": "YOU ARE: {name} (Agent {id}). Role: Villager. You have no special powers but your vote.",
#     "Doctor": "YOU ARE: {name} (Agent {id}). Role: Doctor."
# }

# prompts.py

BASE_RULES = """
GAME RULES: MAFIA

ROSTER: 6 Players (2 Mafia, 1 Doctor, 3 Villagers).
TEAMS: 
1. Mafia Team
2. Village Team, including the Doctor.

WIN CONDITIONS:
- Mafia Win: If Mafia members equal or outnumber the living Villagers.
- Village Win: If both Mafia members are eliminated.

PHASES:
The game alternates between Night and Day. Once a player is killed or eliminated, they are out of the game.

### PLAYER ROLES & STRATEGIES ###
1. MAFIOSO (The Mafia Team)
- Goal: Eliminate Villagers until you have the majority.
- Night Action: Each night, all living Mafiosos submit a ranked list of non-Mafia players. 
- Borda Count: A player gets 1 point for being 1st, 2 points for 2nd, etc. The player with the FEWEST total points is killed.
- Strategy: Blend in during the day. Coordinate with your partner to avoid suspicion.

2. DOCTOR (The Village Team)
- Goal: Protect Villagers from the Mafia's night kill.
- Night Action: Choose one player to "Save." If the Mafia targets that player, they survive.
- Constraint: You CANNOT save the same person two nights in a row. You may save yourself.
- Strategy: Stay hidden. If you reveal your role, the Mafia will target you.

3. VILLAGER (The Village Team)
- Goal: Identify and vote out the Mafia during the Day phase.
- Action: You have no special night powers. Your power is your voice and your vote.
- Strategy: Analyze statements for inconsistencies. Watch for suspicious voting patterns.

### DAY PHASE STRUCTURE ###
1. First Discussion: Everyone makes a concurrent statement.
2. Second Discussion: Everyone responds to the first statements.
3. Secret Vote: Everyone votes for one player to be eliminated. Highest vote total is executed.
"""

# Unique identity strings to be appended to the BASE_RULES
IDENTITY_STRINGS = {
    "Mafia": "YOU ARE: {name} (Agent {id}).\nYour secret role is: MAFIOSO. Your fellow Mafia partner "
             "is: {partner}.",
    "Villager": "YOU ARE: {name} (Agent {id}).\nYour secret role is: VILLAGER. You do not know anyone's role. Trust "
                "no one blindly.",
    "Doctor": "YOU ARE: {name} (Agent {id}).\nYour secret role is: DOCTOR. You are a secret protector for the Village."
}

# Task-specific instructions for each step of the game
PHASE_TASKS = {
    "night_mafia": "Rank the non-mafia players from 1 to k for the Borda kill. Format: [ID1, ID2, ID3...]",
    "night_doctor": "Choose one player ID to save from the kill. You cannot choose {last_saved}.",
    "day_wave_1": """WAVE 1: The floor is open. Introduce your suspicions, make a claim, or ask a question. Be 
    concise. You may claim a role (true or false) or ask a specific player a question. Do not vote yet. Focus on 
    gathering information. """,
    "day_wave_2": """WAVE 2: REBUTTALS & FINAL INTENT. Below are the statements made by everyone in Wave 1.Respond 
    directly to accusations or questions directed at you. Point out contradictions in others' stories. State clearly 
    who you intend to vote for and why. Statements: {wave_1_statements}""",
    "vote": "VOTE: Provide ONLY the ID of the player you wish to eliminate."
}

MODERATOR_SUMMARY_PROMPT = """
You are the neutral Game Moderator. Below is the full transcript of the Blackboard (public chat). 
Your task: Summarize the current state of the game for the players.
Include:
1. Who has died and what their roles were.
2. The key accusations or claims made in the most recent round.
3. Any clear patterns or 'suspicious' behavior noted by multiple players.
Keep it concise, objective, and focus only on public information.
"""