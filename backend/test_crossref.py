import os
import sys

from app.services.crossref_service import verify_title

papers = verify_title("Deep Residual Learning for Image Recognition")
print(papers)
