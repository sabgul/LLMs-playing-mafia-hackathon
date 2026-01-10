from collections import Counter
import random


class MafiaGameState:
    def __init__(self, agents):
        self.agents = agents
        self.round_num = 1
        self.game_over = False
        self.winner = None
        self.last_saved_id = None
        # Track by name for better prompt injection
        self.last_saved_name = "None"

    def get_living_agents(self):
        return [a for a in self.agents if a.is_alive]

    def get_doctor_agent(self):
        """Returns the Agent object of the living Doctor, or None if dead."""
        docs = [a for a in self.get_living_agents() if a.role == "Doctor"]
        return docs[0] if docs else None

    def resolve_night(self, kill_id, save_id):
        self.last_saved_id = save_id
        # Update last_saved_name for the Doctor's next prompt
        save_agent = next((a for a in self.agents if a.id == save_id), None)
        self.last_saved_name = save_agent.name if save_agent else "None"

        if kill_id == save_id:
            return "Morning breaks. A quiet night—nobody died.", None

        victim = next(a for a in self.agents if a.id == kill_id)
        victim.is_alive = False
        return f"Morning breaks. {victim.name} was found dead. They were the {victim.role}.", victim

    def resolve_borda_kill_by_name(self, mafia_responses):
        """
        mafia_responses: List of strings/lists from Mafia agents.
        Logic: 1st place = 1pt, 2nd = 2pt. LOWEST total score wins (is killed).
        """
        living_villagers = [a for a in self.get_living_agents() if a.role != "Mafia"]
        if not living_villagers:
            return None

        village_names = [a.name.lower() for a in living_villagers]
        scores = {a.id: 0 for a in living_villagers}

        # We expect a ranking from each living mafioso
        for response in mafia_responses:
            # If the response is a string, we need to find the names within it in order
            found_names = []
            # This is a simple way to preserve order from the LLM's text
            words = str(response).replace('[', ' ').replace(']', ' ').replace(',', ' ').split()
            for word in words:
                clean_word = word.strip().lower()
                if clean_word in village_names:
                    # Find the ID associated with this name
                    target_agent = next(a for a in living_villagers if a.name.lower() == clean_word)
                    if target_agent.id not in found_names:
                        found_names.append(target_agent.id)

            # Assign points: 1st gets 1, 2nd gets 2, etc.
            for rank, target_id in enumerate(found_names):
                if target_id in scores:
                    scores[target_id] += (rank + 1)

            # Penalty for players not ranked by a Mafioso (give them a high score so they aren't killed)
            for vid in scores:
                if vid not in found_names:
                    scores[vid] += 10

                    # Find the minimum score
        min_score = min(scores.values())
        candidates = [agent_id for agent_id, score in scores.items() if score == min_score]

        # Tie-breaker: Randomly select one
        return random.choice(candidates)

    def resolve_vote_by_name(self, vote_texts):
        living_agents = self.get_living_agents()
        living_names = [a.name for a in living_agents]
        votes_received = []

        for text in vote_texts:
            for name in living_names:
                if name.lower() in text.lower():
                    votes_received.append(name)
                    break

        if not votes_received:
            return "The village could not agree on a name. No one was eliminated.", None

        counts = Counter(votes_received)
        max_votes = counts.most_common(1)[0][1]
        candidates = [name for name, count in counts.items() if count == max_votes]

        eliminated_name = random.choice(candidates)
        victim = next(a for a in self.agents if a.name == eliminated_name)
        victim.is_alive = False

        return f"The Village has spoken. {victim.name} has been eliminated. They were the {victim.role}.", victim

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

# # # TODO mafia game definition (state machine) comes in here
#
# from collections import Counter
# import random
#
#
# class MafiaGameState:
#     def __init__(self, agents):
#         self.agents = agents
#         self.round_num = 1
#         self.game_over = False
#         self.winner = None
#         self.last_saved_id = None
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
#     def resolve_night(self, kill_id, save_id):
#         """Rule: if x == y, nobody dies."""
#         self.last_saved_id = save_id
#         if kill_id == save_id:
#             return "A quiet night—nobody died.", None
#
#         victim = next(a for a in self.agents if a.id == kill_id)
#         victim.is_alive = False
#         return f"{victim.name} (Agent {victim.id}) was killed. They were the {victim.role}.", victim
#
#     def resolve_vote(self, votes):
#         """Rule: Most votes gets executed."""
#         if not votes: return "No one was voted out.", None
#         eliminated_id = Counter(votes).most_common(1)[0][0]
#         victim = next(a for a in self.agents if a.id == eliminated_id)
#         victim.is_alive = False
#         return f"{victim.name} was executed. They were the {victim.role}.", victim
#
#     def resolve_vote_by_name(self, vote_texts):
#         living_agents = self.get_living_agents()
#         living_names = [a.name for a in living_agents]
#         votes_received = []
#
#         for text in vote_texts:
#             for name in living_names:
#                 if name.lower() in text.lower():
#                     votes_received.append(name)
#                     break
#
#         if not votes_received:
#             return "The village could not agree on a name. No one was eliminated.", None
#
#         counts = Counter(votes_received)
#         most_common = counts.most_common()
#
#         max_votes = most_common[0][1]
#         candidates = [name for name, count in most_common if count == max_votes]
#
#         eliminated_name = random.choice(candidates)
#
#         # Find the agent object
#         victim = next(a for a in self.agents if a.name == eliminated_name)
#         victim.is_alive = False
#
#         return f"The Village has voted. {victim.name} has been eliminated. They were the {victim.role}.", victim
#
#     def resolve_borda_kill(self, all_rankings):
#         """
#         all_rankings: List of lists from each Mafia member.
#         Example: [[4, 3, 2, 1], [3, 4, 1, 2]]
#         """
#         if not all_rankings:
#             return None
#
#         scores = Counter()
#         k = len(self.get_living_agents())  # Number of remaining players
#
#         for ranking in all_rankings:
#             for i, target_id in enumerate(ranking):
#                 if i < 4:  # Only top 4 choices as per rules
#                     points = k - i
#                     scores[target_id] += points
#
#         # Return the ID with the highest score
#         return scores.most_common(1)[0][0]
#
#     def check_win(self):
#         living = self.get_living_agents()
#         mafia = [a for a in living if a.role == "Mafia"]
#         villagers = [a for a in living if a.role != "Mafia"]
#
#         if not mafia:
#             self.game_over = True
#             self.winner = "Villagers"
#         elif len(mafia) >= len(villagers):
#             self.game_over = True
#             self.winner = "Mafia"
#         return self.game_over
#
# #
# # class MafiaGameState:
# #     def __init__(self, agents):
# #         self.agents = agents  # List of Agent objects
# #         self.phase = "Night"
# #         self.round_num = 1
# #         self.last_saved_id = None
# #         self.game_over = False
# #         self.winner = None
# #
# #     def get_living_agents(self):
# #         return [a for a in self.agents if a.is_alive]
# #
# #     def get_mafia_agents(self):
# #         return [a for a in self.get_living_agents() if a.role == "Mafia"]
# #
# #     def get_doctor_agent(self):
# #         doc = [a for a in self.get_living_agents() if a.role == "Doctor"]
# #         return doc[0] if doc else None
# #
# #     # --- NIGHT LOGIC ---
# #
# #     def resolve_borda_kill(self, mafia_rankings):
# #         """
# #         mafia_rankings: List of lists, e.g., [[3, 4, 5], [4, 3, 5]]
# #         Scores: 1st place = k, 2nd = k-1, etc.
# #         """
# #         scores = Counter()
# #         k = len(self.get_living_agents())
# #
# #         for ranking in mafia_rankings:
# #             for i, target_id in enumerate(ranking):
# #                 # Only 1st through 4th choices as per rules
# #                 if i < 4:
# #                     scores[target_id] += (k - i)
# #
# #         # Target with highest score is chosen
# #         # TODO shouldnt it be target with the lowest score
# #         if not scores:
# #             return None
# #         return scores.most_common(1)[0][0]
# #
# #     def resolve_night(self, kill_id, save_id):
# #         """Implements the x == y logic and updates the state."""
# #         self.last_saved_id = save_id
# #
# #         if kill_id == save_id:
# #             death_report = "Morning breaks. A quiet night—nobody died."
# #             killed_agent = None
# #         else:
# #             killed_agent = next(a for a in self.agents if a.id == kill_id)
# #             killed_agent.is_alive = False
# #             death_report = f"Morning breaks. {killed_agent.name} (Agent {killed_agent.id}) was found dead. They were " \
# #                            f"the {killed_agent.role}."
# #
# #         return death_report, killed_agent
# #
# #     # --- DAY LOGIC ---
# #
# #     def resolve_vote(self, votes):
# #         """
# #         votes: List of IDs, e.g., [3, 3, 2, 1, 3]
# #         """
# #         if not votes:
# #             return "No one was voted out.", None
# #
# #         vote_counts = Counter(votes)
# #         eliminated_id = vote_counts.most_common(1)[0][0]
# #         victim = next(a for a in self.agents if a.id == eliminated_id)
# #         victim.is_alive = False
# #
# #         report = f"The village has voted. {victim.name} (Agent {victim.id}) was executed. They were the {victim.role}."
# #         return report, victim
# #
# #     # --- WIN CONDITIONS ---
# #
# #     def check_win(self):
# #         living = self.get_living_agents()
# #         mafia = [a for a in living if a.role == "Mafia"]
# #         villagers = [a for a in living if a.role != "Mafia"]
# #
# #         if not mafia:
# #             self.game_over = True
# #             self.winner = "Villagers"
# #             return True
# #         if len(mafia) >= len(villagers):
# #             self.game_over = True
# #             self.winner = "Mafia"
# #             return True
# #         return False
# #
# # # class MafiaGameState:
# # #     def __init__(self, agents):
# # #         self.agents = agents  # List of Agent objects
# # #         self.round_number = 1
# # #         self.phase = "Night"  # Start with Night
# # #         self.blackboard = []  # Public chat history
# # #         self.winner = None
# # #
# # #     def get_living_players(self):
# # #         return [a for a in self.agents if a.is_alive]
# # #
# # #     def resolve_night(self, target_id, save_id):
# # #         """Logic: If player_x == player_y, nobody dies."""
# # #         report = ""
# # #         if target_id == save_id:
# # #             report = "Morning breaks. A quiet night—nobody died."
# # #         else:
# # #             victim = next(a for a in self.agents if a.id == target_id)
# # #             victim.is_alive = False
# # #             report = f"Morning breaks. {victim.name} (Agent {victim.id}) was found dead. They were a {victim.role}."
# # #
# # #         self.blackboard.append(f"SYSTEM: {report}")
# # #         return report
# # #
# # #     def resolve_vote(self, vote_counts):
# # #         """Identifies the player with the most votes."""
# # #         if not vote_counts:
# # #             return "No one was executed today."
# # #
# # #         # Simple majority/highest count logic
# # #         eliminated_id = max(vote_counts, key=vote_counts.get)
# # #         victim = next(a for a in self.agents if a.id == eliminated_id)
# # #         victim.is_alive = False
# # #
# # #         report = f"The village has spoken. {victim.name} (Agent {victim.id}) was executed. They were a {victim.role}."
# # #         self.blackboard.append(f"SYSTEM: {report}")
# # #         return report
# # #
# # #     def check_win_condition(self):
# # #         living = self.get_living_players()
# # #         mafia = [a for a in living if a.role == "Mafia"]
# # #         villagers = [a for a in living if a.role != "Mafia"]
# # #
# # #         if not mafia:
# # #             self.winner = "Villagers"
# # #             return True
# # #         if len(mafia) >= len(villagers):
# # #             self.winner = "Mafia"
# # #             return True
# # #         return False