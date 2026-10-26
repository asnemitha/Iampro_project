import os
import re
import traceback
from typing import List
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


PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"


def get_gemini_models() -> List[str]:
    """
    Return the ordered candidate Gemini models (primary followed by fallback).
    Avoids obsolete or deprecated model IDs and removes duplicates.
    """
    primary = os.getenv("GEMINI_MODEL", PRIMARY_MODEL).strip()
    fallback = os.getenv("GEMINI_FALLBACK_MODEL", FALLBACK_MODEL).strip()
    candidates: List[str] = []
    for model_id in [primary, fallback]:
        if model_id and model_id not in candidates:
            candidates.append(model_id)
    return candidates


# Backward compatibility export
DEFAULT_MODELS = [
    PRIMARY_MODEL,
    FALLBACK_MODEL,
]


def _sanitize_error(error_val) -> str:
    """Remove any embedded API keys or sensitive query tokens from error strings."""
    if not error_val:
        return ""
    text = str(error_val)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and len(api_key.strip()) > 5:
        text = text.replace(api_key.strip(), "[REDACTED_API_KEY]")
    # Redact common key URL parameters and tokens
    text = re.sub(r"(?i)key=[A-Za-z0-9_\-]+", "key=[REDACTED]", text)
    text = re.sub(r"(?i)AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", text)
    text = re.sub(r"(?i)bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", text)
    text = re.sub(r"(?i)x-goog-api-key:\s*[^\s]+", "x-goog-api-key: [REDACTED]", text)
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
    models = get_gemini_models()

    for idx, model_name in enumerate(models):
        is_primary = (idx == 0)
        role = "Primary" if is_primary else "Fallback"
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
            )

            text = response.text
            if text:
                print("\n" + "=" * 80)
                print(f"FULL GEMINI RESPONSE ({role} Model: {model_name})")
                print("=" * 80)
                print(text)
                print("=" * 80)
                return text

        except Exception as e:
            last_error = e
            clean_err = _sanitize_error(e)
            print(f"\n[GeminiService] {role} model '{model_name}' failed: {clean_err[:300]}")

            # Quota/rate-limit errors apply project-wide. Fail fast to avoid worsening rate limits.
            if "429" in clean_err or "RESOURCE_EXHAUSTED" in clean_err:
                raise GeminiQuotaExhaustedError(
                    "Gemini API rate limit reached (HTTP 429 RESOURCE_EXHAUSTED)."
                )

            # For 404 (model not found) or 503 (model unavailable) or other transient errors,
            # fail over to fallback model if available
            continue

    clean_last_err = _sanitize_error(last_error)
    print(f"\n[GeminiService] All Gemini candidate models failed ({', '.join(models)}). Last exception: {clean_last_err[:200]}")
    if "404" in clean_last_err or "NOT_FOUND" in clean_last_err:
        err_msg = f"LLM generation failed: Model not found (HTTP 404 NOT_FOUND). Candidate models ({', '.join(models)}) unavailable."
    elif "503" in clean_last_err or "UNAVAILABLE" in clean_last_err:
        err_msg = f"LLM generation failed: Gemini upstream service unavailable (HTTP 503 UNAVAILABLE)."
    else:
        err_msg = f"LLM generation failed across available models ({', '.join(models)}): {clean_last_err[:200]}"

    raise GeminiServiceError(err_msg)


generate_response = generate_llm_response
