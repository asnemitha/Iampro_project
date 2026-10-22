import sys
import csv
sys.path.insert(0, 'c:/Users/A S Nemitha/Desktop/CiteGuard/backend')

import app.services.citation_verifier as citation_verifier
import app.services.citation_parser as citation_parser
import app.services.crossref_service as crossref_service
import app.services.similarity_service as similarity_service

dataset_path = 'c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification/hard_citation_test_dataset.csv'

def get_b_res(citation):
    try:
        res = citation_verifier.verify_citation(citation)
        return 0 if res.get("exists", False) else 1, res
    except:
        return 1, {}

def get_c_res(citation):
    try:
        parsed = citation_parser.parse_citation(citation)
        doi = parsed.get("doi")
        title = parsed.get("title")
        candidates = []
        if doi:
            res = crossref_service.verify_doi(doi)
            if res: candidates.append(res)
        if title:
            title_res = crossref_service.verify_title(title, rows=5)
            if title_res: candidates.extend(title_res)
        if not candidates: return 1, {}
        best = 0
        best_c = None
        for c in candidates:
            ct = c.get("title")
            if not ct: continue
            sc = similarity_service.compare_titles(title, ct).get("score", 0)
            if sc >= best:
                best = sc
                best_c = c
        return 0 if best >= 80 else 1, {"best_score": best, "best_title": best_c.get("title") if best_c else None}
    except:
        return 1, {}

# Hardcoded rows based on prior knowledge or quick scan
ids_b1_c0 = ["307", "275", "210", "169", "151", "424", "186", "211", "174", "476"]
# Just grab 3 known B0 C1 (since there are only 3 FP for C total!)
# Wait, I don't know the B0 C1 IDs yet. I will scan for them quickly.

with open(dataset_path, 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

b0_c1_rows = []
b1_c0_rows = [r for r in rows if r["id"] in ids_b1_c0]

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass
orig_stdout = sys.stdout

sys.stdout = DummyFile()
for r in rows:
    if len(b0_c1_rows) >= 3: break
    b_p, _ = get_b_res(r["citation"])
    c_p, _ = get_c_res(r["citation"])
    if b_p == 0 and c_p == 1:
        b0_c1_rows.append(r)
sys.stdout = orig_stdout

print("=== 10 EXAMPLES: B prediction = 1 (Hallucinated), C prediction = 0 (Valid) ===")
sys.stdout = DummyFile()
for r in b1_c0_rows:
    bp, br = get_b_res(r["citation"])
    cp, cr = get_c_res(r["citation"])
    sys.stdout = orig_stdout
    print(f"Citation ID: {r['id']}")
    print(f"Error Type: {r['error_type']}")
    print(f"Citation: {r['citation'].strip()}")
    print(f"Crossref candidate returned by B: {br.get('matched_title')}")
    print(f"B decision: {bp}")
    print(f"Crossref candidate(s) returned by C: {cr.get('best_title')}")
    print(f"C title similarity score: {cr.get('best_score')}")
    print(f"C decision: {cp}")
    print("-" * 40)
    sys.stdout = DummyFile()

sys.stdout = orig_stdout
print("\n=== EXAMPLES: B prediction = 0 (Valid), C prediction = 1 (Hallucinated) ===")
sys.stdout = DummyFile()
for r in b0_c1_rows:
    bp, br = get_b_res(r["citation"])
    cp, cr = get_c_res(r["citation"])
    sys.stdout = orig_stdout
    print(f"Citation ID: {r['id']}")
    print(f"Error Type: {r['error_type']}")
    print(f"Citation: {r['citation'].strip()}")
    print(f"Crossref candidate returned by B: {br.get('matched_title')}")
    print(f"B decision: {bp}")
    print(f"Crossref candidate(s) returned by C: {cr.get('best_title')}")
    print(f"C title similarity score: {cr.get('best_score')}")
    print(f"C decision: {cp}")
    print("-" * 40)
    sys.stdout = DummyFile()
sys.stdout = orig_stdout
