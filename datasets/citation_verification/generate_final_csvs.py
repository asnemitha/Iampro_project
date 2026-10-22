import pandas as pd
import json
import os
import csv
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.services import verification_pipeline

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

def load_cache():
    cache_path = Path("reproducible_api_cache.json")
    with open(cache_path, "r", encoding="utf-8") as f:
        return json.load(f)

def calc_metrics(y_true, y_pred, pos_label):
    tp = tn = fp = fn = 0
    for t, p in zip(y_true, y_pred):
        if t == pos_label and p == pos_label:
            tp += 1
        elif t != pos_label and p != pos_label:
            tn += 1
        elif t != pos_label and p == pos_label:
            fp += 1
        elif t == pos_label and p != pos_label:
            fn += 1
            
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return [total, tp, tn, fp, fn, accuracy, precision, recall, f1]

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
        
    configs = [
        ("Current CiteGuard", False, False),
        ("CiteGuard + Author Fix", True, False),
        ("CiteGuard + Venue Fix", False, True),
        ("CiteGuard + Author + Venue Fix", True, True)
    ]
    
    detailed_data = []
    
    # Store predictions for each config
    preds = {c[0]: [] for c in configs}
    y_true_orig = [] # 1=Hallucinated, 0=Valid (based on dataset)
    
    with patch("app.services.verification_pipeline.verify_doi", side_effect=mock_verify_doi), \
         patch("app.services.verification_pipeline.retrieve_candidates", side_effect=mock_retrieve_candidates):
         
        for row in rows:
            CURRENT_CID = row["id"]
            true_h = int(row["ground_truth"]) # 1=Hallucinated, 0=Valid
            y_true_orig.append(true_h)
            
            row_results = {}
            for name, use_a, use_v in configs:
                llm_formatted = f"[1]\n{row['citation']}"
                sys.stdout = DummyFile()
                try:
                    res = verification_pipeline.verify_response(llm_formatted, use_author_fix=use_a, use_venue_fix=use_v)
                except Exception:
                    res = []
                sys.stdout = sys.__stdout__
                
                if not res:
                    pred_h = 1 # Hallucinated
                    res_dict = {}
                else:
                    pred_valid = res[0].get("citation_accurate", False)
                    pred_h = 0 if pred_valid else 1
                    res_dict = res[0]
                    
                preds[name].append(pred_h)
                row_results[name] = res_dict
            
            # Use the combined fix for the detailed metrics
            comb = row_results["CiteGuard + Author + Venue Fix"]
            detailed_data.append({
                "citation_id": CURRENT_CID,
                "ground_truth": true_h,
                "error_type": row.get("error_type", ""),
                "current_citeguard_prediction": preds["Current CiteGuard"][-1],
                "author_fix_prediction": preds["CiteGuard + Author Fix"][-1],
                "venue_fix_prediction": preds["CiteGuard + Venue Fix"][-1],
                "combined_fix_prediction": preds["CiteGuard + Author + Venue Fix"][-1],
                "hallucination_positive_prediction": preds["CiteGuard + Author + Venue Fix"][-1], # 1=Hallucinated
                "title_similarity": comb.get("title_similarity", ""),
                "author_similarity": comb.get("author_similarity", ""),
                "venue_similarity": comb.get("venue_match", ""),
                "year_match": comb.get("year_match", ""),
                "doi_match": comb.get("doi_match", ""),
                "final_reason": "; ".join(comb.get("reason", [])) if comb else ""
            })
            
    # Write final_detailed_results.csv
    detailed_df = pd.DataFrame(detailed_data)
    detailed_df.to_csv("final_detailed_results.csv", index=False)
    
    # Write final_results.csv
    results_rows = []
    # User's mapped definitions: 
    # For Valid-Positive: Valid=1, Hallucinated=0. 
    # In original dataset, 1=Hallucinated, 0=Valid.
    # So to calculate Valid-Positive, we map true_h and pred_h: 0->1, 1->0
    
    y_true_valid = [1 if y == 0 else 0 for y in y_true_orig]
    
    for name, _, _ in configs:
        pred_h = preds[name]
        pred_valid = [1 if y == 0 else 0 for y in pred_h]
        
        # Valid-Positive
        m_valid = calc_metrics(y_true_valid, pred_valid, pos_label=1)
        results_rows.append([name, "valid"] + m_valid)
        
        # Hallucinated-Positive
        m_hall = calc_metrics(y_true_orig, pred_h, pos_label=1)
        results_rows.append([name, "hallucinated"] + m_hall)
        
    res_df = pd.DataFrame(results_rows, columns=["configuration", "positive_class", "total", "tp", "tn", "fp", "fn", "accuracy", "precision", "recall", "f1"])
    res_df.to_csv("final_results.csv", index=False)
    
    print("CSV generation complete.")

if __name__ == "__main__":
    main()
