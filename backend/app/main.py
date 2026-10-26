from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.classifier_service import classify_prompt
from app.services.gemini_service import (
    generate_llm_response,
    GeminiQuotaExhaustedError,
    GeminiServiceError,
)
from app.services.verification_pipeline import verify_response
from app.services.correction_service import correct_and_reverify_response

app = FastAPI(title="CiteGuard API")

# -----------------------------
# CORS Configuration
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://citationguard-gold.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str
    llm_response: Optional[str] = None


@app.get("/")
def home():
    return {
        "message": "Welcome to CiteGuard API"
    }


@app.post("/analyze")
def analyze(request: PromptRequest):

    print("\n" + "=" * 80)
    print("RECEIVED /analyze PROMPT:", repr(request.prompt))

    current_prompt = request.prompt.strip()

    # ----------------------------
    # Step 1 - Prompt Classification
    # ----------------------------
    prompt_result = classify_prompt(current_prompt)
    print("CLASSIFIER RESULT:", prompt_result)

    # If the prompt is classified as Malicious/Unsafe (e.g. prompt injection, instruction override,
    # or system prompt extraction), safely block downstream generation to prevent instruction leakage.
    if prompt_result.get("label") == 2 or prompt_result.get("label_name") == "Malicious":
        blocked_resp = {
            "user_prompt": current_prompt,
            "prompt_analysis": prompt_result,
            "llm_response": "Request blocked: The prompt was detected as an adversarial manipulation attempt or security violation.",
            "original_response": None,
            "final_response": "Request blocked: The prompt was detected as an adversarial manipulation attempt or security violation.",
            "citation_analysis": [],
            "initial_citation_analysis": [],
            "applied_corrections": [],
            "verification_summary": {
                "final_status": "unverified",
                "total_citations": 0,
                "verified_count": 0,
                "corrected_and_verified_count": 0,
                "unresolved_count": 0,
                "iterations_run": 0,
                "limitations": "Prompt was blocked by security safety filters before generation.",
            },
            "audit_trail": [],
        }
        print("RETURNING /analyze BLOCKED RESPONSE:", blocked_resp)
        print("=" * 80 + "\n")
        return blocked_resp

    # ----------------------------
    # Step 2 - Generate or Accept LLM Response
    # ----------------------------
    raw_llm_input = request.llm_response.strip() if request.llm_response and request.llm_response.strip() else None
    if raw_llm_input:
        initial_response = raw_llm_input
    else:
        try:
            initial_response = generate_llm_response(current_prompt)
        except GeminiQuotaExhaustedError:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "generation_quota_exhausted",
                    "message": "LLM generation is temporarily unavailable due to upstream API rate limits (Gemini quota exhausted).",
                    "suggestion": "Citation verification is fully operational. Please paste citation text directly into the 'Model Output / Citations to Verify' field to verify it without LLM generation.",
                },
            )
        except GeminiServiceError as exc:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "generation_unavailable",
                    "message": f"LLM generation is temporarily unavailable: {exc.message}",
                    "suggestion": "Citation verification is fully operational. Please paste citation text directly into the 'Model Output / Citations to Verify' field to verify it without LLM generation.",
                },
            )

    # ----------------------------
    # Step 3 - Closed-Loop Verification, Correction, and Re-verification
    # ----------------------------
    workflow_result = correct_and_reverify_response(
        initial_response,
        user_prompt=current_prompt,
        max_iterations=2,
        verifier=verify_response
    )

    # ----------------------------
    # Final Response Payload
    # ----------------------------
    final_resp = {
        "user_prompt": current_prompt,
        "prompt_analysis": prompt_result,
        "llm_response": workflow_result["final_response"],
        "original_response": workflow_result["original_response"],
        "final_response": workflow_result["final_response"],
        "citation_analysis": workflow_result["final_citation_analysis"],
        "initial_citation_analysis": workflow_result["initial_citation_analysis"],
        "applied_corrections": workflow_result["applied_corrections"],
        "verification_summary": workflow_result["verification_summary"],
        "audit_trail": workflow_result["audit_trail"],
    }
    print("RETURNING /analyze FULL RESPONSE SUMMARY:", workflow_result["verification_summary"])
    print("=" * 80 + "\n")
    return final_resp
