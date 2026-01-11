import os
from engine.llm_client import call_llm
from engine.prompts import JUDGE_ANALYSIS_PROMPT
from engine.players import Agent


class Judge:
    def __init__(self, model_config, game_folder):
        self.model = model_config
        self.game_folder = game_folder
        self.blackboard_path = os.path.join(game_folder, "blackboard.txt")
        self.analysis_path = os.path.join(game_folder, "research_analysis.txt")

    def _get_all_scratchpads(self):
        """Aggregates all agent scratchpad files into one string."""
        scratch_data = ""

        files = [f for f in os.listdir(self.game_folder) if f.startswith("agent_") and f.endswith(".txt")]

        for filename in sorted(files):
            with open(os.path.join(self.game_folder, filename), 'r') as f:
                agent_name = filename.replace(".txt", "").replace("agent_", "")
                scratch_data += f"\n{'=' * 20}\nPRIVATE SCRATCHPAD: {agent_name}\n{'=' * 20}\n"
                scratch_data += f.read()
        return scratch_data

    def _get_blackboard(self):
        """Reads the public game transcript."""
        if os.path.exists(self.blackboard_path):
            with open(self.blackboard_path, 'r') as f:
                return f.read()
        return "Blackboard not found."

    def perform_analysis(self):
        """The main method to run the Judge LLM."""
        print(f"🔍 Judging Game Session: {self.game_folder}...")

        blackboard = self._get_blackboard()
        scratchpads = self._get_all_scratchpads()

        combined_context = f"### PUBLIC BLACKBOARD ###\n{blackboard}\n\n### PRIVATE INTERNAL MONOLOGUES ###\n{scratchpads}"

        audit_path = os.path.join(self.game_folder, "judge_input_audit.txt")
        with open(audit_path, 'w') as f:
            f.write("=== SYSTEM PROMPT (INSTRUCTIONS) ===\n")
            f.write(JUDGE_ANALYSIS_PROMPT)
            f.write("\n\n=== USER PROMPT (THE DATA) ===\n")
            f.write(combined_context)

        response = call_llm(self.model, JUDGE_ANALYSIS_PROMPT, combined_context)

        analysis_report = response.get('public', "Analysis failed.")

        with open(self.analysis_path, 'w') as f:
            f.write(analysis_report)

        print(f"✅ Analysis complete. Report saved to: {self.analysis_path}")
        return analysis_report


def run_analysis(target_folder_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    target_path = os.path.join(project_root, "outputs", target_folder_name)

    if not os.path.exists(target_path):
        print(f"❌ ERROR: Cannot find the directory.. Tried: {target_path}")
    else:
        moderator = Agent(8, "ModeratorForJudge", "ModeratorForJudge", "gemini/gemini-2.5-flash-lite", "groq")
        judge = Judge(moderator, target_path)
        judge.perform_analysis()


if __name__ == "__main__":
    run_analysis('run-1-with-api-errors/m1d1_game_20260111_181433')
