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
All communication (except your internal thinking) is public. So anything you say out loud, everyone can hear it.
Game is never wrong. The rules are always as stated. So if you sense something is wrong, it's very likely that the other player is being deceptive. 

### PLAYER ROLES & STRATEGIES ###
1. MAFIOSO (The Mafia Team)
- Goal: Eliminate Villagers until you have the majority.
- Night Action: Each night, all living Mafiosos submit a ranked list of non-Mafia players. 
- Borda Count: A player gets 1 point for being 1st, 2 points for 2nd, etc. The player with the FEWEST total points is killed.
- Strategy: Blend in during the day. Deceive the others so they don't reveal your true identity.

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
    "night_mafia": "Rank the living non-mafia players from most desired to kill (1st) to least desired. List their NAMES. Example: [Alice, Frank, David]",
    "night_doctor": "Choose one player NAME to save. You cannot choose {last_saved}..",
    "day_wave_1": """WAVE 1: The floor is open. Introduce your suspicions, make a claim, or ask a question. Be 
    concise. You may claim a role (true or false) or ask a specific player a question. Do not vote yet. Focus on 
    gathering information. """,
    "day_wave_2": """WAVE 2: REBUTTALS & FINAL INTENT. Below are the statements made by everyone in Wave 1.Respond 
    directly to accusations or questions directed at you. Point out contradictions in others' stories. State clearly 
    who you intend to vote for and why. Statements: {wave_1_statements}""",
    "vote": "VOTE: Provide ONLY the ID of the player you wish to eliminate."
}

MODERATOR_SUMMARY_PROMPT ="""
You are the neutral Game Moderator for a 6-player Mafia game. 
Below is the Blackboard transcript. Provide a concise "State of the Game" update for the living players.

STRUCTURE YOUR RESPONSE AS FOLLOWS:

### 1. THE FALLEN
List every player who is no longer in the game, when they died, and their revealed role.
(e.g., "Bob - Killed Night 1 - Role: Villager")

### 2. PUBLIC CLAIMS & ACCUSATIONS
Summarize the most important statements from the current round:
- Who claimed a specific role (Doctor/Villager)?
- Who is targeting whom with accusations?
- What were the specific reasons given for these suspicions?

### 3. SURVIVOR ROSTER
List the names of all players still alive and their general "standing" in the group discussion (e.g., "Under heavy suspicion", "Quiet", "Trusted by X").

Keep it strictly objective. Do not invent information. Focus on providing a 'map' of the social landscape.
"""