import random
from collections import Counter


class MafiaGameState:
    def __init__(self, agents):
        self.agents = agents
        self.round_num = 1
        self.game_over = False
        self.winner = None
        self.last_saved_id = None
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
        living_villagers = [a for a in self.get_living_agents() if a.role != "Mafia"]
        if not living_villagers:
            return None

        village_names = [a.name.lower() for a in living_villagers]
        # Initialize all potential victims with 0 points
        scores = {a.id: 0 for a in living_villagers}

        for idx, response in enumerate(mafia_responses):
            found_names_ids = []
            words = str(response).replace('[', ' ').replace(']', ' ').replace(',', ' ').split()

            for word in words:
                clean_word = word.strip().strip('.').strip('!').lower()
                if clean_word in village_names:
                    target_agent = next(a for a in living_villagers if a.name.lower() == clean_word)
                    if target_agent.id not in found_names_ids:
                        found_names_ids.append(target_agent.id)

            # Assign Borda points
            for rank, target_id in enumerate(found_names_ids):
                points = rank + 1
                scores[target_id] += points

            # Apply the +10 penalty for anyone NOT mentioned by THIS Mafioso
            for vid in scores:
                if vid not in found_names_ids:
                    scores[vid] += 10

        if not scores:
            return None

        min_score = min(scores.values())
        candidates = [agent_id for agent_id, score in scores.items() if score == min_score]

        final_victim_id = random.choice(candidates)
        return final_victim_id

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
        elif not villagers:
            self.game_over = True
            self.winner = "Mafia"
        elif len(mafia) == 1 and len(villagers) == 1:
            self.game_over = True
            self.winner = "Tie. One mafioso and one villager left."

        return self.game_over
