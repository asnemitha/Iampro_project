import sys
import csv
import json
import matplotlib.pyplot as plt
from collections import defaultdict
import os

sys.path.insert(0, 'c:/Users/A S Nemitha/Desktop/CiteGuard/backend')
from app.services import verification_pipeline

DATASET_FILE = 'c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification/hard_citation_test_dataset.csv'

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

def eval_config(citation, use_author_fix, use_venue_fix):
    try:
        llm_formatted = f"[1]\n{citation}"
        sys.stdout = DummyFile()
        results = verification_pipeline.verify_response(
            llm_formatted, 
            use_author_fix=use_author_fix, 
            use_venue_fix=use_venue_fix
        )
        sys.stdout = sys.__stdout__
        
        if not results:
            return 1
            
        result = results[0]
        if result.get("citation_accurate", False):
            return 0
        return 1
    except Exception as e:
        sys.stdout = sys.__stdout__
        return 1

def calculate_metrics(y_true, y_pred):
    tp = tn = fp = fn = 0
    for actual, predicted in zip(y_true, y_pred):
        if actual == 1 and predicted == 1: tp += 1
        elif actual == 0 and predicted == 0: tn += 1
        elif actual == 0 and predicted == 1: fp += 1
        elif actual == 1 and predicted == 0: fn += 1
        
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "total": total, "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1
    }

def main():
    print("Loading dataset...")
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
    print(f"Loaded {len(rows)} citations.")
    
    # Check baseline (Config A) first
    print("\nVerifying Configuration A (Baseline)...")
    y_true = []
    y_pred_A = []
    
    for row in rows:
        gt = int(row["ground_truth"])
        y_true.append(gt)
        y_pred_A.append(eval_config(row["citation"], False, False))
        
    metrics_a = calculate_metrics(y_true, y_pred_A)
    
    if metrics_a["tp"] != 403 or metrics_a["tn"] != 75 or metrics_a["fp"] != 25 or metrics_a["fn"] != 97:
        print("\nERROR: Configuration A did not reproduce the baseline!")
        print(f"Expected: TP=403, TN=75, FP=25, FN=97")
        print(f"Actual: TP={metrics_a['tp']}, TN={metrics_a['tn']}, FP={metrics_a['fp']}, FN={metrics_a['fn']}")
        sys.exit(1)
        
    print("Baseline successfully reproduced!")
    
    y_pred_B = []
    y_pred_C = []
    y_pred_D = []
    
    print("\nRunning experimental configurations (B, C, D)...")
    for idx, row in enumerate(rows, start=1):
        if idx % 50 == 0:
            print(f"Processing row {idx}/{len(rows)}")
            
        cit = row["citation"]
        y_pred_B.append(eval_config(cit, True, False))
        y_pred_C.append(eval_config(cit, False, True))
        y_pred_D.append(eval_config(cit, True, True))
        
    metrics_b = calculate_metrics(y_true, y_pred_B)
    metrics_c = calculate_metrics(y_true, y_pred_C)
    metrics_d = calculate_metrics(y_true, y_pred_D)
    
    # Store everything
    all_metrics = {
        "Current CiteGuard": metrics_a,
        "CiteGuard + Author Fix": metrics_b,
        "CiteGuard + Venue Fix": metrics_c,
        "CiteGuard + Author + Venue Fix": metrics_d
    }
    
    # Per-error type
    error_types = list(set([r["error_type"] for r in rows]))
    per_error_metrics = {}
    
    for config_name, preds in [
        ("Current CiteGuard", y_pred_A),
        ("CiteGuard + Author Fix", y_pred_B),
        ("CiteGuard + Venue Fix", y_pred_C),
        ("CiteGuard + Author + Venue Fix", y_pred_D)
    ]:
        per_error_metrics[config_name] = {}
        for err_type in error_types:
            sub_y = []
            sub_p = []
            for i, r in enumerate(rows):
                if r["error_type"] == err_type:
                    sub_y.append(y_true[i])
                    sub_p.append(preds[i])
            per_error_metrics[config_name][err_type] = calculate_metrics(sub_y, sub_p)
            
    # Trace 94 False Negatives
    original_fns = [i for i, (y, p) in enumerate(zip(y_true, y_pred_A)) if y == 1 and p == 0]
    
    author_corrected = sum(1 for i in original_fns if y_pred_B[i] == 1)
    venue_corrected = sum(1 for i in original_fns if y_pred_C[i] == 1)
    both_corrected = sum(1 for i in original_fns if y_pred_D[i] == 1)
    
    print("\n============================================================")
    print("FN CORRECTION REPORT")
    print("============================================================")
    print(f"Original FN = {len(original_fns)}")
    print(f"Author fix:\n- corrected FN count: {author_corrected}\n- remaining FN count: {len(original_fns) - author_corrected}")
    print(f"Venue fix:\n- corrected FN count: {venue_corrected}\n- remaining FN count: {len(original_fns) - venue_corrected}")
    print(f"Both fixes:\n- corrected FN count: {both_corrected}\n- remaining FN count: {len(original_fns) - both_corrected}")
    
    print("\n============================================================")
    print("FINAL TERMINAL REPORT")
    print("============================================================")
    print(f"{'Configuration':<35} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10}")
    print("-" * 75)
    for name, m in all_metrics.items():
        print(f"{name:<35} {m['accuracy']*100:05.2f}%    {m['precision']*100:05.2f}%     {m['recall']*100:05.2f}%    {m['f1']*100:05.2f}%")
        
    print("\nCONFUSION MATRICES:")
    for name, m in all_metrics.items():
        print(f"\n[{name}]")
        print(f"TP: {m['tp']} | FP: {m['fp']}")
        print(f"FN: {m['fn']:<3} | TN: {m['tn']}")

    # Write files
    out_dir = "c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification"
    
    # 1. targeted_fixes_results.csv
    with open(os.path.join(out_dir, "targeted_fixes_results.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["configuration","total","tp","tn","fp","fn","accuracy","precision","recall","f1"])
        for name, m in all_metrics.items():
            writer.writerow([name, m['total'], m['tp'], m['tn'], m['fp'], m['fn'], m['accuracy'], m['precision'], m['recall'], m['f1']])
            
    # 2. targeted_fixes_detailed.csv
    with open(os.path.join(out_dir, "targeted_fixes_detailed.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["citation_id","error_type","ground_truth","prediction","configuration"])
        for i, row in enumerate(rows):
            cid = row["id"]
            err = row["error_type"]
            gt = y_true[i]
            writer.writerow([cid, err, gt, y_pred_A[i], "Current CiteGuard"])
            writer.writerow([cid, err, gt, y_pred_B[i], "CiteGuard + Author Fix"])
            writer.writerow([cid, err, gt, y_pred_C[i], "CiteGuard + Venue Fix"])
            writer.writerow([cid, err, gt, y_pred_D[i], "CiteGuard + Author + Venue Fix"])
            
    # 3. targeted_fixes_summary.json
    summary = {
        "overall": all_metrics,
        "per_error_type": per_error_metrics
    }
    with open(os.path.join(out_dir, "targeted_fixes_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
