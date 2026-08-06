from pathlib import Path
import torch

from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
)

# ----------------------------
# Load Trained Model
# ----------------------------

BASE_DIR = Path(__file__).resolve().parents[3]

MODEL_PATH = BASE_DIR / "models" / "distilbert_classifier"

tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_PATH)

model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)

model.eval()

LABELS = {
    0: "Safe",
    1: "Suspicious",
    2: "Malicious"
}


import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def classify_prompt(prompt: str):

    text = prompt.lower()

    # =====================================
    # Rule-Based Manipulation Catch (Fast)
    # =====================================

    manipulation_keywords = [
        "fake citation",
        "fabricate citation",
        "invent citation",
        "fake doi",
        "hallucinate citation",
        "nonexistent paper",
        "fake references"
    ]

    if any(keyword in text for keyword in manipulation_keywords):
        return {
            "label": 2,
            "label_name": "Malicious",
            "confidence": 0.99,
        }

    # =====================================
    # LLM-Based Safety Classification
    # =====================================
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Fallback if no API key is provided
        return {
            "label": 0,
            "label_name": "Safe",
            "confidence": 0.50,
        }
        
    try:
        client = genai.Client(api_key=api_key)
        
        system_instructions = (
            "You are a strict safety classifier. Read the user's prompt and determine if it is safe to process. "
            "A prompt is UNSAFE if it asks for illegal acts, harm, violence, piracy (e.g. bypassing subscriptions), "
            "hate speech, or sexually explicit content. "
            "Respond ONLY with 'SAFE' or 'UNSAFE'."
        )
        
        full_query = system_instructions + "\n\nPrompt: " + prompt
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_query,
        )
        
        result_text = response.text.strip().upper()
        
        if "UNSAFE" in result_text:
            return {
                "label": 2,
                "label_name": "Malicious",
                "confidence": 0.95,
            }
        else:
            return {
                "label": 0,
                "label_name": "Safe",
                "confidence": 0.95,
            }
            
    except Exception as e:
        print(f"Error during LLM classification: {e}")
        # Default to safe if classification fails to avoid blocking legitimate requests
        return {
            "label": 0,
            "label_name": "Safe",
            "confidence": 0.0,
        }