import os
import re
import traceback
from dotenv import load_dotenv
from google import genai

load_dotenv()


class GeminiServiceError(Exception):
    """Base exception for Gemini service failures."""
    def __init__(self, message: str, is_quota_error: bool = False):
        super().__init__(message)
        self.message = message
        self.is_quota_error = is_quota_error


class GeminiQuotaExhaustedError(GeminiServiceError):
    """Raised when Gemini returns HTTP 429 RESOURCE_EXHAUSTED."""
    def __init__(self, message: str = "Gemini API rate limit reached (HTTP 429 RESOURCE_EXHAUSTED)."):
        super().__init__(message, is_quota_error=True)


DEFAULT_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]


def _sanitize_error(error_val) -> str:
    """Remove any embedded API keys or sensitive query tokens from error strings."""
    if not error_val:
        return ""
    text = str(error_val)
    text = re.sub(r"(?i)key=[A-Za-z0-9_\-]+", "key=[REDACTED]", text)
    text = re.sub(r"(?i)AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", text)
    return text


def generate_llm_response(prompt: str) -> str:
    """
    Generate response using Google Gemini API with fallback model failover.
    Raises GeminiQuotaExhaustedError or GeminiServiceError upon failure.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[GeminiService] Error: GEMINI_API_KEY environment variable not set.")
        raise GeminiServiceError("GEMINI_API_KEY environment variable is not configured.")

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
            clean_err = _sanitize_error(e)
            print(f"\n[GeminiService] Model '{model_name}' failed: {clean_err[:300]}")

            # Quota/rate-limit errors apply project-wide. Fail fast to avoid worsening rate limits.
            if "429" in clean_err or "RESOURCE_EXHAUSTED" in clean_err:
                raise GeminiQuotaExhaustedError(
                    "Gemini API rate limit reached (HTTP 429 RESOURCE_EXHAUSTED)."
                )

            if "404" in clean_err or "NOT_FOUND" in clean_err:
                continue
            continue

    clean_last_err = _sanitize_error(last_error)
    print(f"\n[GeminiService] All Gemini candidate models failed. Last exception: {clean_last_err[:200]}")
    raise GeminiServiceError(f"LLM generation failed across available models: {clean_last_err[:200]}")
