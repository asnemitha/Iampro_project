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
            
            # True=0 (Valid citation according to dataset)
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
                # y_pred = 1
                pred_valid = False
            else:
                pred_valid = results[0].get("citation_accurate", False)
            
            if not pred_valid:
                # Model predicted 1 (citation_accurate=False)
                # True=0, Pred=1 -> This is a False Positive!
                result = results[0] if results else {}
                fp_details.append({
                    "id": CURRENT_CID,
                    "error_type": row.get("error_type", "Unknown"),
                    "citation": row["citation"],
                    "matched_title": result.get("matched_title"),
                    "title_similarity": result.get("title_similarity"),
                    "author_similarity": result.get("author_similarity"),
                    "year_match": result.get("year_match"),
                    "venue_similarity": result.get("venue_match"), 
                    "doi_match": result.get("doi_match"),
                    "reasons": result.get("reason", [])
                })

    for fp in fp_details:
        print("="*60)
        for k, v in fp.items():
            print(f"{k}: {v}")
            
    print(f"Total FP found: {len(fp_details)}")

if __name__ == "__main__":
    main()
