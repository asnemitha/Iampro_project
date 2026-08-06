import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def generate_llm_response(prompt: str):
    """
    Generate response using Google Gemini API
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
        
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
    
    try:
        # Using gemini-2.5-flash as it's the recommended default for text tasks
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
        )

        text = response.text
        
        print("\n" + "=" * 80)
        print("FULL GEMINI RESPONSE")
        print("=" * 80)
        print(text)
        print("=" * 80)

        return text
    except Exception as e:
        print(f"\nError generating LLM response: {e}")
        return "I'm sorry, I cannot process this request at the moment due to safety filters or rate limits."