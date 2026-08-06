from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR / "backend"))

from app.services.crossref_service import (
    search_by_doi,
    search_by_title,
)

print("=" * 60)
print("Testing DOI Search")
print("=" * 60)

doi_result = search_by_doi(
    "10.1038/s41586-021-03819-2"
)

if doi_result:
    print("Title:")
    print(doi_result["title"][0])

print("\n")

print("=" * 60)
print("Testing Title Search")
print("=" * 60)

results = search_by_title(
    "Highly accurate protein structure prediction with AlphaFold"
)

for i, paper in enumerate(results[:3], start=1):

    print(f"\nResult {i}")
    print("Title:", paper.get("title", [""])[0])
    print("DOI:", paper.get("DOI"))
    print("Publisher:", paper.get("publisher"))