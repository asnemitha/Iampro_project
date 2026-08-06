from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR / "backend"))

from app.services.gemini_service import generate_llm_response

prompt = """
What is Artificial Intelligence?
Give two academic references in IEEE format.
"""

response = generate_llm_response(prompt)

print("=" * 60)
print(response)
print("=" * 60)