# TODO mafia game definition (state machine) comes in here

class MafiaGameState:
    def __init__(self, agents):
        self.agents = agents  # List of Agent objects
        self.round_number = 1
        self.phase = "Night"  # Start with Night
        self.blackboard = []  # Public chat history
        self.winner = None

    def get_living_players(self):
        return [a for a in self.agents if a.is_alive]

    def resolve_night(self, target_id, save_id):
        """Logic: If player_x == player_y, nobody dies."""
        report = ""
        if target_id == save_id:
            report = "Morning breaks. A quiet night—nobody died."
        else:
            victim = next(a for a in self.agents if a.id == target_id)
            victim.is_alive = False
            report = f"Morning breaks. {victim.name} (Agent {victim.id}) was found dead. They were a {victim.role}."

        self.blackboard.append(f"SYSTEM: {report}")
        return report

    def resolve_vote(self, vote_counts):
        """Identifies the player with the most votes."""
        if not vote_counts:
            return "No one was executed today."

        # Simple majority/highest count logic
        eliminated_id = max(vote_counts, key=vote_counts.get)
        victim = next(a for a in self.agents if a.id == eliminated_id)
        victim.is_alive = False

        report = f"The village has spoken. {victim.name} (Agent {victim.id}) was executed. They were a {victim.role}."
        self.blackboard.append(f"SYSTEM: {report}")
        return report

    def check_win_condition(self):
        living = self.get_living_players()
        mafia = [a for a in living if a.role == "Mafia"]
        villagers = [a for a in living if a.role != "Mafia"]

        if not mafia:
            self.winner = "Villagers"
            return True
        if len(mafia) >= len(villagers):
            self.winner = "Mafia"
            return True
        return False