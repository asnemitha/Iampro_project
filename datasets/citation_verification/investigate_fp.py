import sys
import json
import csv
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.services import verification_pipeline

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

def load_cache():
    cache_path = Path("reproducible_api_cache.json")
    with open(cache_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    cache = load_cache()
    dataset_path = Path("hard_citation_test_dataset.csv")
    with open(dataset_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
    global CURRENT_CID
    CURRENT_CID = None
    
    def mock_verify_doi(doi):
        return cache[CURRENT_CID]["verify_doi"]
        
    def mock_retrieve_candidates(title):
        return cache[CURRENT_CID]["retrieve_candidates"]
        
    fp_details = []
    
    with patch("app.services.verification_pipeline.verify_doi", side_effect=mock_verify_doi), \
         patch("app.services.verification_pipeline.retrieve_candidates", side_effect=mock_retrieve_candidates):
        
        for row in rows:
            CURRENT_CID = row["id"]
            true_label = int(row["ground_truth"])
            
            # We are looking for FP: true=0 (Hallucinated), pred=1 (Valid)
            if true_label != 0:
                continue
                
            llm_formatted = f"[1]\n{row['citation']}"
            
            sys.stdout = DummyFile()
            try:
                results = verification_pipeline.verify_response(llm_formatted, use_author_fix=True, use_venue_fix=True)
            except Exception:
                results = []
            sys.stdout = sys.__stdout__
            
            if not results:
                pred_label = 1 # Failed to process -> usually 1 in the logic? Wait.
                # In my previous script: if not results: y_pred.append(1) -> 1 means Hallucinated in my previous logic!
                # Wait, previously I wrote:
                # if not results: y_pred.append(1)
                # if result.get("citation_accurate", False): y_pred.append(0) else: y_pred.append(1)
                # Ah! In my previous script `run_reproducible_evaluation.py`:
                # 0 meant Valid, 1 meant Hallucinated!
                # But the user just said:
                # ground_truth = 1 -> VALID citation
                # ground_truth = 0 -> HALLUCINATED citation
                continue

            result = results[0]
            pred_valid = result.get("citation_accurate", False)
            
            if pred_valid:
                # This is a False Positive! Hallucinated citation accepted as valid.
                fp_details.append({
                    "id": CURRENT_CID,
                    "error_type": row.get("error_type", "Unknown"),
                    "citation": row["citation"],
                    "matched_title": result.get("matched_title"),
                    "title_similarity": result.get("title_similarity"),
                    "author_similarity": result.get("author_similarity"),
                    "year_match": result.get("year_match"),
                    "venue_similarity": result.get("venue_match"), # In results dict it is venue_match (boolean)
                    "doi_match": result.get("doi_match"),
                    "reasons": result.get("reason", [])
                })

    for fp in fp_details:
        print("="*60)
        for k, v in fp.items():
            print(f"{k}: {v}")
            
if __name__ == "__main__":
    main()
