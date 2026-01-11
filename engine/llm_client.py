from litellm import completion
from dotenv import load_dotenv

load_dotenv()


def call_llm(agent, system_prompt, user_prompt):
    """
    Unified caller for Gemini (Players) and Groq (Moderator).
    """
    try:
        extra_params = {}
        if "gemini" in agent.model:
            extra_params["reasoning_effort"] = "high"

        response = completion(
            model=agent.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            **extra_params
        )

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