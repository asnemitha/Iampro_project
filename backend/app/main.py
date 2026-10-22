from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.classifier_service import classify_prompt
from app.services.gemini_service import generate_llm_response
from app.services.verification_pipeline import verify_response

app = FastAPI(title="CiteGuard API")

# -----------------------------
# CORS Configuration
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str


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
            "citation_analysis": []
        }
        print("RETURNING /analyze BLOCKED RESPONSE:", blocked_resp)
        print("=" * 80 + "\n")
        return blocked_resp

    # ----------------------------
    # Step 2 - Generate LLM Response
    # ----------------------------
    llm_response = generate_llm_response(current_prompt)

    # ----------------------------
    # Step 3 - Citation Verification
    # ----------------------------
    citation_results = verify_response(llm_response, user_prompt=current_prompt)

    # ----------------------------
    # Final Response
    # ----------------------------
    final_resp = {
        "user_prompt": current_prompt,
        "prompt_analysis": prompt_result,
        "llm_response": llm_response,
        "citation_analysis": citation_results
    }
    print("RETURNING /analyze FULL RESPONSE:", final_resp)
    print("=" * 80 + "\n")
    return final_resp