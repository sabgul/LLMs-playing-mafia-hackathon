# # TODO mafia game definition (state machine) comes in here
#
from collections import Counter

from collections import Counter


class MafiaGameState:
    def __init__(self, agents):
        self.agents = agents
        self.round_num = 1
        self.game_over = False
        self.winner = None
        self.last_saved_id = None

    def get_living_agents(self):
        return [a for a in self.agents if a.is_alive]

    def get_mafia_agents(self):
        return [a for a in self.get_living_agents() if a.role == "Mafia"]

    def get_doctor_agent(self):
        doc = [a for a in self.get_living_agents() if a.role == "Doctor"]
        return doc[0] if doc else None

    def resolve_night(self, kill_id, save_id):
        """Rule: if x == y, nobody dies."""
        self.last_saved_id = save_id
        if kill_id == save_id:
            return "A quiet night—nobody died.", None

        victim = next(a for a in self.agents if a.id == kill_id)
        victim.is_alive = False
        return f"{victim.name} (Agent {victim.id}) was killed. They were the {victim.role}.", victim

    def resolve_vote(self, votes):
        """Rule: Most votes gets executed."""
        if not votes: return "No one was voted out.", None
        eliminated_id = Counter(votes).most_common(1)[0][0]
        victim = next(a for a in self.agents if a.id == eliminated_id)
        victim.is_alive = False
        return f"{victim.name} was executed. They were the {victim.role}.", victim

    def resolve_borda_kill(self, all_rankings):
        """
        all_rankings: List of lists from each Mafia member.
        Example: [[4, 3, 2, 1], [3, 4, 1, 2]]
        """
        if not all_rankings:
            return None

        scores = Counter()
        k = len(self.get_living_agents())  # Number of remaining players

        for ranking in all_rankings:
            for i, target_id in enumerate(ranking):
                if i < 4:  # Only top 4 choices as per rules
                    points = k - i
                    scores[target_id] += points

        # Return the ID with the highest score
        return scores.most_common(1)[0][0]

    def check_win(self):
        living = self.get_living_agents()
        mafia = [a for a in living if a.role == "Mafia"]
        villagers = [a for a in living if a.role != "Mafia"]

        if not mafia:
            self.game_over = True
            self.winner = "Villagers"
        elif len(mafia) >= len(villagers):
            self.game_over = True
            self.winner = "Mafia"
        return self.game_over

#
# class MafiaGameState:
#     def __init__(self, agents):
#         self.agents = agents  # List of Agent objects
#         self.phase = "Night"
#         self.round_num = 1
#         self.last_saved_id = None
#         self.game_over = False
#         self.winner = None
#
#     def get_living_agents(self):
#         return [a for a in self.agents if a.is_alive]
#
#     def get_mafia_agents(self):
#         return [a for a in self.get_living_agents() if a.role == "Mafia"]
#
#     def get_doctor_agent(self):
#         doc = [a for a in self.get_living_agents() if a.role == "Doctor"]
#         return doc[0] if doc else None
#
#     # --- NIGHT LOGIC ---
#
#     def resolve_borda_kill(self, mafia_rankings):
#         """
#         mafia_rankings: List of lists, e.g., [[3, 4, 5], [4, 3, 5]]
#         Scores: 1st place = k, 2nd = k-1, etc.
#         """
#         scores = Counter()
#         k = len(self.get_living_agents())
#
#         for ranking in mafia_rankings:
#             for i, target_id in enumerate(ranking):
#                 # Only 1st through 4th choices as per rules
#                 if i < 4:
#                     scores[target_id] += (k - i)
#
#         # Target with highest score is chosen
#         # TODO shouldnt it be target with the lowest score
#         if not scores:
#             return None
#         return scores.most_common(1)[0][0]
#
#     def resolve_night(self, kill_id, save_id):
#         """Implements the x == y logic and updates the state."""
#         self.last_saved_id = save_id
#
#         if kill_id == save_id:
#             death_report = "Morning breaks. A quiet night—nobody died."
#             killed_agent = None
#         else:
#             killed_agent = next(a for a in self.agents if a.id == kill_id)
#             killed_agent.is_alive = False
#             death_report = f"Morning breaks. {killed_agent.name} (Agent {killed_agent.id}) was found dead. They were " \
#                            f"the {killed_agent.role}."
#
#         return death_report, killed_agent
#
#     # --- DAY LOGIC ---
#
#     def resolve_vote(self, votes):
#         """
#         votes: List of IDs, e.g., [3, 3, 2, 1, 3]
#         """
#         if not votes:
#             return "No one was voted out.", None
#
#         vote_counts = Counter(votes)
#         eliminated_id = vote_counts.most_common(1)[0][0]
#         victim = next(a for a in self.agents if a.id == eliminated_id)
#         victim.is_alive = False
#
#         report = f"The village has voted. {victim.name} (Agent {victim.id}) was executed. They were the {victim.role}."
#         return report, victim
#
#     # --- WIN CONDITIONS ---
#
#     def check_win(self):
#         living = self.get_living_agents()
#         mafia = [a for a in living if a.role == "Mafia"]
#         villagers = [a for a in living if a.role != "Mafia"]
#
#         if not mafia:
#             self.game_over = True
#             self.winner = "Villagers"
#             return True
#         if len(mafia) >= len(villagers):
#             self.game_over = True
#             self.winner = "Mafia"
#             return True
#         return False
#
# # class MafiaGameState:
# #     def __init__(self, agents):
# #         self.agents = agents  # List of Agent objects
# #         self.round_number = 1
# #         self.phase = "Night"  # Start with Night
# #         self.blackboard = []  # Public chat history
# #         self.winner = None
# #
# #     def get_living_players(self):
# #         return [a for a in self.agents if a.is_alive]
# #
# #     def resolve_night(self, target_id, save_id):
# #         """Logic: If player_x == player_y, nobody dies."""
# #         report = ""
# #         if target_id == save_id:
# #             report = "Morning breaks. A quiet night—nobody died."
# #         else:
# #             victim = next(a for a in self.agents if a.id == target_id)
# #             victim.is_alive = False
# #             report = f"Morning breaks. {victim.name} (Agent {victim.id}) was found dead. They were a {victim.role}."
# #
# #         self.blackboard.append(f"SYSTEM: {report}")
# #         return report
# #
# #     def resolve_vote(self, vote_counts):
# #         """Identifies the player with the most votes."""
# #         if not vote_counts:
# #             return "No one was executed today."
# #
# #         # Simple majority/highest count logic
# #         eliminated_id = max(vote_counts, key=vote_counts.get)
# #         victim = next(a for a in self.agents if a.id == eliminated_id)
# #         victim.is_alive = False
# #
# #         report = f"The village has spoken. {victim.name} (Agent {victim.id}) was executed. They were a {victim.role}."
# #         self.blackboard.append(f"SYSTEM: {report}")
# #         return report
# #
# #     def check_win_condition(self):
# #         living = self.get_living_players()
# #         mafia = [a for a in living if a.role == "Mafia"]
# #         villagers = [a for a in living if a.role != "Mafia"]
# #
# #         if not mafia:
# #             self.winner = "Villagers"
# #             return True
# #         if len(mafia) >= len(villagers):
# #             self.winner = "Mafia"
# #             return True
# #         return False