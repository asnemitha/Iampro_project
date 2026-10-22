import sys
import json
import csv
import time
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.services.citation_extractor import extract_citations
from app.services.citation_parser import parse_citation
from app.services.crossref_service import verify_doi
from app.services.multi_source_retriever import retrieve_candidates

def build_cache():
    dataset_path = Path("hard_citation_test_dataset.csv")
    output_path = Path("reproducible_api_cache.json")
    
    print(f"Reading dataset from {dataset_path}...")
    with open(dataset_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
    cache = {}
    
    print(f"Building cache for {len(rows)} citations...")
    
    for i, row in enumerate(rows):
        cid = row["id"]
        citation_text = row["citation"]
        
        # We must format exactly as the pipeline does to extract properly
        llm_formatted = f"[1]\n{citation_text}"
        extracted = extract_citations(llm_formatted)
        
        if not extracted:
            cache[cid] = {"verify_doi": None, "retrieve_candidates": []}
            continue
            
        parsed = parse_citation(extracted[0])
        
        # 1. verify_doi
        doi_result = None
        if parsed["doi"]:
            doi_result = verify_doi(parsed["doi"])
            
        # 2. retrieve_candidates
        candidates_result = []
        if parsed["title"]:
            candidates_result = retrieve_candidates(parsed["title"])
            
        cache[cid] = {
            "verify_doi": doi_result,
            "retrieve_candidates": candidates_result
        }
        
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(rows)}...")
            
    print(f"Saving cache to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
        
    print("Cache built successfully!")

if __name__ == "__main__":
    build_cache()
