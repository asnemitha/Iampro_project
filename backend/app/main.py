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

    # ----------------------------
    # Step 1 - Prompt Classification
    # ----------------------------
    prompt_result = classify_prompt(request.prompt)

    # ----------------------------
    # Step 2 - Generate LLM Response
    # ----------------------------
    llm_response = generate_llm_response(request.prompt)

    # ----------------------------
    # Step 3 - Citation Verification
    # ----------------------------
    citation_results = verify_response(llm_response)

    # ----------------------------
    # Final Response
    # ----------------------------
    return {
        "user_prompt": request.prompt,
        "prompt_analysis": prompt_result,
        "llm_response": llm_response,
        "citation_analysis": citation_results
    }