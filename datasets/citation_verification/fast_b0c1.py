import sys
import csv
sys.path.insert(0, 'c:/Users/A S Nemitha/Desktop/CiteGuard/backend')
from run_ablation import eval_config_b, eval_config_c
import app.services.citation_verifier as citation_verifier
import app.services.citation_parser as citation_parser
import app.services.crossref_service as crossref_service
import app.services.similarity_service as similarity_service

dataset_path = 'c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification/hard_citation_test_dataset.csv'

with open(dataset_path, 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

# First find which ones are Valid in ground_truth (only 100 rows)
valid_rows = [r for r in rows if r["ground_truth"] == "0"]

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass
orig_stdout = sys.stdout

print("=== EXAMPLES WHERE B=0 (Valid) and C=1 (Hallucinated) ===")

sys.stdout = DummyFile()
found = []
for r in valid_rows:
    b_pred = eval_config_b(r["citation"])
    c_pred = eval_config_c(r["citation"])
    
    if b_pred == 0 and c_pred == 1:
        found.append(r)
sys.stdout = orig_stdout

for r in found:
    sys.stdout = DummyFile()
    br = citation_verifier.verify_citation(r["citation"])
    
    parsed = citation_parser.parse_citation(r["citation"])
    doi = parsed.get("doi")
    title = parsed.get("title")
    candidates = []
    if doi:
        res = crossref_service.verify_doi(doi)
        if res: candidates.append(res)
    if title:
        title_res = crossref_service.verify_title(title, rows=5)
        if title_res: candidates.extend(title_res)
    best = 0
    best_c = None
    for c in candidates:
        ct = c.get("title")
        if not ct: continue
        sc = similarity_service.compare_titles(title, ct).get("score", 0)
        if sc >= best:
            best = sc
            best_c = c
            
    sys.stdout = orig_stdout
    
    print(f"Citation ID: {r['id']}")
    print(f"Error Type: {r['error_type']}")
    print(f"Citation: {r['citation'].strip()}")
    print(f"Crossref candidate returned by B: {br.get('matched_title')}")
    print(f"B decision: 0")
    print(f"Crossref candidate(s) returned by C: {best_c.get('title') if best_c else 'None'}")
    print(f"C title similarity score: {best}")
    print(f"C decision: 1")
    print("-" * 60)
