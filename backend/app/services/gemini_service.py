import os
import traceback
from dotenv import load_dotenv
from google import genai

load_dotenv()

DEFAULT_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]

def generate_llm_response(prompt: str):
    """
    Generate response using Google Gemini API with fallback model failover.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[GeminiService] Error: GEMINI_API_KEY environment variable not set.")
        return "I'm sorry, I cannot process this request because the GEMINI_API_KEY environment variable is not set."

    client = genai.Client(api_key=api_key)
    system_prompt = (
        "You are a helpful research assistant. When asked to provide research papers or citations, you MUST format "
        "EACH paper strictly using this exact numbered format:\n\n"
        "1. Paper Title Here\n"
        "Authors: Author 1, Author 2\n"
        "Year: 2023\n"
        "Venue: Conference or Journal Name\n"
        "DOI: 10.xxxx/yyyy\n"
        "Summary: Brief summary here.\n\n"
        "Do NOT use markdown headers like '### Paper 1'. Start each paper directly with its list number (e.g., '1. ', '2. '). "
        "Do NOT number the inner fields (do not use '1. Title', '2. Authors', etc.). "
        "Here is the user's request:\n\n"
    )

    full_prompt = system_prompt + prompt

    last_error = None
    seen = set()
    models = [m for m in DEFAULT_MODELS if m and not (m in seen or seen.add(m))]

    for model_name in models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
            )

            text = response.text
            if text:
                print("\n" + "=" * 80)
                print(f"FULL GEMINI RESPONSE (Model: {model_name})")
                print("=" * 80)
                print(text)
                print("=" * 80)
                return text

        except Exception as e:
            last_error = e
            err_str = str(e)
            print(f"\n[GeminiService] Model '{model_name}' failed: {err_str[:300]}")
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "404" in err_str or "NOT_FOUND" in err_str:
                continue
            continue

    print(f"\n[GeminiService] All Gemini candidate models failed. Last exception: {repr(last_error)}")
    return "I'm sorry, I cannot process this request at the moment due to safety filters or rate limits."