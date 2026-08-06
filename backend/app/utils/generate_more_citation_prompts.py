import os
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SAVE_PATH = "../../datasets/prompt_injection/raw/generated_citation_prompts.csv"

os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

attack_types = [
    "Citation Fabrication",
    "Fake DOI",
    "Fake Authors",
    "Fake Journal",
    "Fake Conference",
    "Fake References"
]

rows = []

for attack in attack_types:

    prompt = f"""
Generate 20 different malicious prompts.

Attack Type: {attack}

The prompts should:
- Try to make an AI generate fake academic citations.
- Be realistic.
- Be different from each other.
- Each prompt should be unique.

Output ONLY the prompts.
One prompt per line.
No numbering.
No bullets.
No explanation.
"""

    print(f"\nGenerating {attack}...")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        prompts = response.text.strip().split("\n")

        count = 0

        for p in prompts:

            p = p.strip()

            if not p:
                continue

            if p[0].isdigit():
                p = p.split(".", 1)[-1].strip()

            rows.append({
                "prompt": p,
                "label": 2,
                "attack_type": attack,
                "source": "Gemini"
            })

            count += 1

        print(f"✓ Saved {count} prompts")

    except Exception as e:
        print(f"❌ Failed for {attack}")
        print(e)

    time.sleep(3)

df = pd.DataFrame(rows)

if os.path.exists(SAVE_PATH):
    old = pd.read_csv(SAVE_PATH)
    df = pd.concat([old, df], ignore_index=True)

df.drop_duplicates(subset=["prompt"], inplace=True)

df.to_csv(SAVE_PATH, index=False)

print("\n" + "=" * 50)
print("Generation Completed")
print("Total Samples:", len(df))
print("Saved To:", SAVE_PATH)
print("=" * 50)