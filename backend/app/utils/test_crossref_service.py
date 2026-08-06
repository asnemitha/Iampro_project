from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR / "backend"))

from app.services.crossref_service import verify_doi, verify_title

print("=" * 60)
print("Testing DOI")
print("=" * 60)

doi = "10.1038/s41586-021-03819-2"

result = verify_doi(doi)

print(result)

print("\n")

print("=" * 60)
print("Testing Title")
print("=" * 60)

results = verify_title(
    "Highly accurate protein structure prediction with AlphaFold"
)

for i, paper in enumerate(results, start=1):

    print(f"\nResult {i}")
    print(paper)