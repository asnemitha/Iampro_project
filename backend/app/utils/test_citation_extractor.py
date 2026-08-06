from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR / "backend"))

from app.services.citation_extractor import extract_citations

sample_text = """
Artificial Intelligence is transforming healthcare.

References

[1] J. Smith, "Artificial Intelligence in Healthcare",
IEEE Access, vol. 9, pp. 100-110, 2023.
DOI: 10.1109/ACCESS.2023.1234567

[2] A. Kumar,
"Deep Learning for Medical Imaging",
IEEE Transactions on Medical Imaging,
2022.

https://ieeexplore.ieee.org/document/1234567

arXiv:2401.12345
"""

citations = extract_citations(sample_text)

print("=" * 60)

for i, citation in enumerate(citations, start=1):
    print(f"\nCitation {i}")
    print(citation)

print("\nTotal Extracted:", len(citations))