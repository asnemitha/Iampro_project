from fastapi import APIRouter
from pydantic import BaseModel

from app.services.classifier_service import classify_prompt

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str

@router.post("/analyze")
def analyze(request: PromptRequest):

    result = classify_prompt(request.prompt)

    return {
        "user_prompt": request.prompt,
        "prediction": result
    }