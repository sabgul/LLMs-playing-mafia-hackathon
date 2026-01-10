import random
from collections import Counter


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
