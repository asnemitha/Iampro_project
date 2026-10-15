import sys
import json
import csv
import time
from pathlib import Path
from unittest.mock import patch

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.services import verification_pipeline

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

def load_cache():
    cache_path = Path("reproducible_api_cache.json")
    if not cache_path.exists():
        print("ERROR: reproducible_api_cache.json not found.")
        sys.exit(1)
    with open(cache_path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_metrics(y_true, y_pred):
    tp = tn = fp = fn = 0
    for true, pred in zip(y_true, y_pred):
        if true == 1 and pred == 1:
            tp += 1
        elif true == 0 and pred == 0:
            tn += 1
        elif true == 0 and pred == 1:
            fp += 1
        elif true == 1 and pred == 0:
            fn += 1
            
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": accuracy, "precision": precision,
        "recall": recall, "f1": f1
    }

def main():
    print("Loading cache...")
    cache = load_cache()
    
    print("Loading dataset...")
    dataset_path = Path("hard_citation_test_dataset.csv")
    with open(dataset_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
    y_true = [int(r["ground_truth"]) for r in rows]
    
    # Global state for mocks
    global CURRENT_CID
    CURRENT_CID = None
    
    def mock_verify_doi(doi, *args, **kwargs):
        return cache[CURRENT_CID]["verify_doi"]
        
    def mock_retrieve_candidates(title, *args, **kwargs):
        return cache[CURRENT_CID]["retrieve_candidates"]
        
    def eval_config(use_author, use_venue):
        y_pred = []
        global CURRENT_CID
        
        # Patch the functions INSIDE verification_pipeline module namespace
        with patch("app.services.verification_pipeline.verify_doi", side_effect=mock_verify_doi), \
             patch("app.services.verification_pipeline.retrieve_candidates", side_effect=mock_retrieve_candidates):
            
            for row in rows:
                CURRENT_CID = row["id"]
                citation = row["citation"]
                llm_formatted = f"[1]\n{citation}"
                
                sys.stdout = DummyFile()
                try:
                    results = verification_pipeline.verify_response(
                        llm_formatted, 
                        use_author_fix=use_author, 
                        use_venue_fix=use_venue
                    )
                except Exception as e:
                    results = []
                sys.stdout = sys.__stdout__
                
                if not results:
                    y_pred.append(1)
                    continue
                    
                result = results[0]
                if result.get("citation_accurate", False):
                    y_pred.append(0)
                else:
                    y_pred.append(1)
                    
        return y_pred

    print("\nRunning Configuration 1 (Current CiteGuard)...")
    y_pred_A = eval_config(use_author=False, use_venue=False)
    metrics_a = calculate_metrics(y_true, y_pred_A)
    
    # The cache is static, so if baseline was 97 FN during cache building, it will be exactly that.
    # We will log the exact metrics obtained from the baseline for reference.
    baseline_fn = metrics_a["fn"]
    print(f"Baseline established. TP={metrics_a['tp']}, TN={metrics_a['tn']}, FP={metrics_a['fp']}, FN={baseline_fn}")
    
    print("Running Configuration 2 (CiteGuard + Author Fix)...")
    y_pred_B = eval_config(use_author=True, use_venue=False)
    
    print("Running Configuration 3 (CiteGuard + Venue Fix)...")
    y_pred_C = eval_config(use_author=False, use_venue=True)
    
    print("Running Configuration 4 (CiteGuard + Author + Venue Fix)...")
    y_pred_D = eval_config(use_author=True, use_venue=True)
    
    metrics_b = calculate_metrics(y_true, y_pred_B)
    metrics_c = calculate_metrics(y_true, y_pred_C)
    metrics_d = calculate_metrics(y_true, y_pred_D)
    
    print("\n============================================================")
    print("FN CORRECTION REPORT")
    print("============================================================")
    print(f"Original FN = {baseline_fn}")
    
    print("Author fix:")
    corrected_b = baseline_fn - metrics_b["fn"]
    print(f"- corrected FN count: {corrected_b}")
    print(f"- remaining FN count: {metrics_b['fn']}")
    
    print("Venue fix:")
    corrected_c = baseline_fn - metrics_c["fn"]
    print(f"- corrected FN count: {corrected_c}")
    print(f"- remaining FN count: {metrics_c['fn']}")
    
    print("Both fixes:")
    corrected_d = baseline_fn - metrics_d["fn"]
    print(f"- corrected FN count: {corrected_d}")
    print(f"- remaining FN count: {metrics_d['fn']}")
    
    print("\n============================================================")
    print("FINAL TERMINAL REPORT (REPRODUCIBLE CACHE MODE)")
    print("============================================================")
    header = f"{'Configuration':<35} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10}"
    print(header)
    print("-" * len(header))
    
    configs = [
        ("Current CiteGuard", metrics_a),
        ("CiteGuard + Author Fix", metrics_b),
        ("CiteGuard + Venue Fix", metrics_c),
        ("CiteGuard + Author + Venue Fix", metrics_d)
    ]
    
    for name, m in configs:
        acc = f"{m['accuracy']*100:.2f}%"
        pre = f"{m['precision']*100:.2f}%"
        rec = f"{m['recall']*100:.2f}%"
        f1  = f"{m['f1']*100:.2f}%"
        print(f"{name:<35} {acc:<10} {pre:<10} {rec:<10} {f1:<10}")

    print("\nCONFUSION MATRICES:")
    for name, m in configs:
        print(f"\n[{name}]")
        print(f"TP: {m['tp']} | FP: {m['fp']}")
        print(f"FN: {m['fn']}  | TN: {m['tn']}")

if __name__ == "__main__":
    main()
