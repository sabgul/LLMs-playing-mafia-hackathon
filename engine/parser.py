import re


def extract_single_id(text):
    """
    Finds the first integer in a string.
    Used for: Doctor saves, Voting, and simple Kill targets.
    Example: 'I vote for 3' -> 3
    """
    if not text:
        return None
    # finds one or more digits
    match = re.search(r'\d+', str(text))
    return int(match.group()) if match else None


def extract_rankings(text):
    """
    Finds all integers in a string and returns them as a list.
    Used for: Mafia Borda Count rankings.
    Example: 'My choices: 3, 4, 1, 2' -> [3, 4, 1, 2]
    """
    if not text:
        return []
    # finds all sequences of digits
    numbers = re.findall(r'\d+', str(text))
    return [int(n) for n in numbers]


def extract_name(text, living_names):
    """Finds a player name within a block of text."""
    for name in living_names:
        if name.lower() in text.lower():
            return name
    return None


def clean_llm_json(text):
    """
    If you decide to use JSON mode, this strips the ```json tags
    that models often add.
    """
    return text.replace("```json", "").replace("```", "").strip()