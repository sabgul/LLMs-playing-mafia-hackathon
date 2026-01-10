import os
from litellm import completion
from dotenv import load_dotenv


def connectivity_test():
    load_dotenv()

    try:
        print("Testing Gemini API connection...")
        response = completion(
            model="gemini/gemini-2.5-flash",
            messages=[{"role": "user", "content": "Hello, are you there?"}]
        )
        print("SUCCESS! Response:", response.choices[0].message.content)
    except Exception as e:
        print("FAILURE!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")


if __name__ == "__main__":
    connectivity_test()