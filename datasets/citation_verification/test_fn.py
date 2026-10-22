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
        results = verification_pipeline.verify_response(llm_formatted)
        sys.stdout = sys.__stdout__
        if not results: return 1
        result = results[0]
        if result.get("citation_accurate", False): return 0
        return 1
    except Exception as e:
        sys.stdout = sys.__stdout__
        return 1

with open('c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification/hard_citation_test_dataset.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

fn = 0
for i, row in enumerate(rows):
    if int(row["ground_truth"]) == 1:
        pred = eval_config_e(row["citation"])
        if pred == 0: fn += 1

print(f"FN count using verification_pipeline (no flags): {fn}")
