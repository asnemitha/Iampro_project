from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR / "backend"))

from app.services.citation_parser import parse_citation

sample = """
[1] J. Smith, A. Kumar

"Artificial Intelligence in Healthcare"

IEEE Access

2023

DOI:10.1109/ACCESS.2023.1234567
"""

parsed = parse_citation(sample)

print("=" * 60)

for key, value in parsed.items():
    print(f"{key}: {value}")

print("=" * 60)