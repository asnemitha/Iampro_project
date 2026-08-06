from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR / "backend"))

from app.services.citation_verifier import verify_text

sample = """
DOI: 10.1038/s41586-021-03819-2
"""

result = verify_text(sample)

print("=" * 60)
print(result)
print("=" * 60)