import sys
import os

from app.services.verification_pipeline import verify_response

llm_response = """Here are two highly influential IEEE research papers related to computer vision:

---

### Paper 1: Deep Residual Learning for Image Recognition

1.  **Title:** Deep Residual Learning for Image Recognition
2.  **Authors:** Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
3.  **Conference:** IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016
4.  **Abstract (Summary):**
    As deep neural networks become deeper, they become harder to train.
"""

results = verify_response(llm_response)
for res in results:
    print("Paper Exists:", res["paper_exists"])
    print("Title Similarity:", res["title_similarity"])
    print("Author Similarity:", res["author_similarity"])
    print("DOI Match:", res["doi_match"])
    print("Citation Accurate:", res["citation_accurate"])
    print("Hallucination Type:", res["hallucination_type"])
    print(res["reason"])
