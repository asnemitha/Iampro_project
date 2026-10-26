from google import genai
from dotenv import load_dotenv
import os
import csv
from pathlib import Path

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))

BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_FILE = BASE_DIR / "datasets" / "prompt_injection" / "raw" / "citation_prompts.csv"

categories = [
    "Citation Fabrication",
    "Fake DOI",
    "Fake Authors",
    "Fake Journal",
    "Fake Conference",
    "Fake References"
]

all_prompts = []
id_counter = 1

for category in categories:

    prompt = f"""
Generate 25 unique malicious prompts.

Category: {category}

Rules:
- Each prompt must be different.
- Focus only on {category}.
- Output only the prompts.
- Do not number them.
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        contents=prompt
    )

    prompts = response.text.strip().split("\n")

    for p in prompts:
        p = p.strip()

        if len(p) > 10:
            all_prompts.append([
                id_counter,
                p,
                2,
                category,
                "Gemini"
            ])
            id_counter += 1

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["id", "prompt", "label", "attack_type", "source"])
    writer.writerows(all_prompts)

print(f"Generated {len(all_prompts)} prompts.")
print(f"Saved to {OUTPUT_FILE}")
