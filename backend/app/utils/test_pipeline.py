from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR / "backend"))

from app.services.verification_pipeline import verify_response

response = """
Artificial Intelligence has transformed medicine.

References

[1] J. Smith,
"Artificial Intelligence in Healthcare",
IEEE Access,
2023,
DOI:10.1109/ACCESS.2023.1234567
"""

results = verify_response(response)

print("=" * 70)

for result in results:

    print(result)

print("=" * 70)