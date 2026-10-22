import sys, csv, json
sys.path.insert(0, 'c:/Users/A S Nemitha/Desktop/CiteGuard/backend')
from app.services.verification_pipeline import verify_response
import app.services.citation_parser as citation_parser

dataset_path = 'c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification/hard_citation_test_dataset.csv'

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass
orig_stdout = sys.stdout

def get_examples(ground_truth_val, count=10):
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r['ground_truth'] == str(ground_truth_val)]
    return rows[:count]

print('=== GROUND TRUTH = 0 (VALID CITATIONS) ===')
for row in get_examples(0):
    sys.stdout = DummyFile()
    try:
        results = verify_response(row['citation'])
    except Exception as e:
        results = [{'error': str(e)}]
    sys.stdout = orig_stdout
    print(f"ID: {row['id']}")
    print(f"Citation: {row['citation'].strip()}")
    print(f"Ground Truth: {row['ground_truth']}")
    if results:
        res = results[0]
        acc = res.get('citation_accurate')
        print(f"Raw output: {json.dumps(res, indent=2)}")
        print(f"citation_accurate: {acc}")
        pred = 0 if acc else 1
        print(f"Prediction: {pred}")
        if pred == 0:
            print("Explanation: citation_accurate is True.")
        else:
            print("Explanation: citation_accurate is False or missing.")
    else:
        print("Raw output: []")
        print("Prediction: 1")
        print("Explanation: No results returned.")
    print('-'*40)

print('\n=== GROUND TRUTH = 1 (HALLUCINATED CITATIONS) ===')
for row in get_examples(1):
    sys.stdout = DummyFile()
    try:
        results = verify_response(row['citation'])
    except Exception as e:
        results = [{'error': str(e)}]
    sys.stdout = orig_stdout
    print(f"ID: {row['id']}")
    print(f"Citation: {row['citation'].strip()}")
    print(f"Ground Truth: {row['ground_truth']}")
    if results:
        res = results[0]
        acc = res.get('citation_accurate')
        print(f"Raw output: {json.dumps(res, indent=2)}")
        print(f"citation_accurate: {acc}")
        pred = 0 if acc else 1
        print(f"Prediction: {pred}")
    else:
        print("Raw output: []")
    print('-'*40)
