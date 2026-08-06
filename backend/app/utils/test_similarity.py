from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR / "backend"))

from app.services.similarity_service import *

title1 = "Highly accurate protein structure prediction with AlphaFold"
title2 = "Highly accurate protein structure prediction with AlphaFold"

authors1 = [
    "John Jumper",
    "Richard Evans"
]

authors2 = [
    "John Jumper",
    "Richard Evans"
]

print("=" * 60)

title = compare_titles(title1, title2)

print("Title Score:", title["score"])

author_score = compare_authors(authors1, authors2)

print("Author Score:", author_score)

year_match = compare_year(2021, 2021)

print("Year Match:", year_match)

hallucination = hallucination_score(
    title["score"],
    author_score,
    year_match
)

print("\nHallucination Score:", hallucination)

print("=" * 60)