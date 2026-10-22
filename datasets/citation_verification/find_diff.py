import sys
import csv
sys.path.insert(0, 'c:/Users/A S Nemitha/Desktop/CiteGuard/backend')
from app.services import verification_pipeline

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

def eval_config_e(citation):
    try:
        llm_formatted = f"[1]\n{citation}"
        sys.stdout = DummyFile()
        results = verification_pipeline.verify_response(llm_formatted, use_author_fix=False, use_venue_fix=False)
        sys.stdout = sys.__stdout__
        if not results: return 1
        result = results[0]
        if result.get("citation_accurate", False): return 0
        return 1
    except Exception as e:
        sys.stdout = sys.__stdout__
        return 1

with open('c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification/ablation_detailed_results.csv', 'r', encoding='utf-8') as f:
    ablation_rows = list(csv.DictReader(f))

with open('c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification/hard_citation_test_dataset.csv', 'r', encoding='utf-8') as f:
    dataset_rows = {r["id"]: r for r in csv.DictReader(f)}

full_citeguard_preds = {}
for r in ablation_rows:
    if r["configuration"] == "Full CiteGuard":
        full_citeguard_preds[r["citation_id"]] = int(r["prediction"])

print("Comparing predictions...")
diffs = []
for cid, row in dataset_rows.items():
    old_pred = full_citeguard_preds[cid]
    new_pred = eval_config_e(row["citation"])
    if old_pred != new_pred:
        diffs.append((cid, row["error_type"], old_pred, new_pred))
        print(f"Diff! ID: {cid}, Error: {row['error_type']}, Old Pred: {old_pred}, New Pred: {new_pred}")

print(f"Found {len(diffs)} differences.")
