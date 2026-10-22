import sys
import csv
import json
sys.path.insert(0, 'c:/Users/A S Nemitha/Desktop/CiteGuard/backend')
from run_ablation import eval_config_e

dataset_path = 'c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification/hard_citation_test_dataset.csv'

def get_examples(ground_truth_val, count=10):
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r['ground_truth'] == str(ground_truth_val)]
    return rows[:count]

# Suppress pipeline prints
class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass
orig_stdout = sys.stdout

rows = get_examples(0, 10) + get_examples(1, 10)

tp = tn = fp = fn = 0

for row in rows:
    gt = int(row['ground_truth'])
    
    sys.stdout = DummyFile()
    pred = eval_config_e(row['citation'])
    sys.stdout = orig_stdout
    
    if gt == 1 and pred == 1: tp += 1
    elif gt == 0 and pred == 0: tn += 1
    elif gt == 0 and pred == 1: fp += 1
    elif gt == 1 and pred == 0: fn += 1

print(f"Test on 20 rows (10 valid, 10 hallucinated):")
print(f"TP: {tp}")
print(f"TN: {tn}")
print(f"FP: {fp}")
print(f"FN: {fn}")

accuracy = (tp + tn) / 20
print(f"Accuracy: {accuracy}")
