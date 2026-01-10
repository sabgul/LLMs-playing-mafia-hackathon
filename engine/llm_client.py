# TODO llm api calls go here, API boilerplate

import os
from litellm import completion
from dotenv import load_dotenv

load_dotenv()


def call_llm(agent, system_prompt, user_prompt):
    """
    Unified caller for Gemini (Players) and Groq (Moderator).
    """
    try:
        # Determine if we should trigger 'Thinking' (only for Gemini)
        # Gemini 2.5/3 uses 'reasoning_effort' or 'thinking'
        extra_params = {}
        if "gemini" in agent.model:
            # This triggers the internal deliberation process
            extra_params["reasoning_effort"] = "high"

        response = completion(
            model=agent.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            **extra_params
        )

        # Extracting the content
        # .content is the public message
        # .reasoning_content is the 'Thinking' process (Gemini only)
        public_message = response.choices[0].message.content
        internal_thought = getattr(response.choices[0].message, 'reasoning_content', "")

        return {
            "public": public_message,
            "thought": internal_thought
        }

    except Exception as e:
        return {"error": str(e), "public": "API ERROR", "thought": ""}