import sys
import csv
import json
sys.path.insert(0, 'c:/Users/A S Nemitha/Desktop/CiteGuard/backend')

import app.services.citation_verifier as citation_verifier
import app.services.citation_parser as citation_parser
import app.services.crossref_service as crossref_service
import app.services.similarity_service as similarity_service

dataset_path = 'c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification/hard_citation_test_dataset.csv'

def get_config_b_debug(citation):
    try:
        result = citation_verifier.verify_citation(citation)
        pred = 0 if result.get("exists", False) else 1
        return pred, result
    except Exception as e:
        return 1, {"error": str(e)}

def get_config_c_debug(citation):
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
            if title_res:
                candidates.extend(title_res)
                
        if not candidates:
            return 1, {"candidates": [], "best_score": 0, "parsed_title": title}
            
        best_title_score = 0
        best_candidate = None
        for candidate in candidates:
            cand_title = candidate.get("title")
            if not cand_title: continue
            
            sim_res = similarity_service.compare_titles(title, cand_title)
            score = sim_res.get("score", 0)
            if score >= best_title_score:
                best_title_score = score
                best_candidate = candidate
                
        pred = 0 if best_title_score >= 80 else 1
        return pred, {"candidates": candidates, "best_score": best_title_score, "best_candidate": best_candidate, "parsed_title": title}
    except Exception as e:
        return 1, {"error": str(e)}

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

def main():
    orig_stdout = sys.stdout
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    b1_c0_count = 0
    b0_c1_count = 0
    
    print("=== EXAMPLES WHERE B=1 (Hallucinated) and C=0 (Valid) ===")
    
    for row in rows:
        if b1_c0_count >= 10:
            break
            
        cit = row["citation"]
        
        sys.stdout = DummyFile()
        b_pred, b_res = get_config_b_debug(cit)
        c_pred, c_res = get_config_c_debug(cit)
        sys.stdout = orig_stdout
        
        if b_pred == 1 and c_pred == 0:
            b1_c0_count += 1
            print(f"ID: {row['id']} | Error Type: {row['error_type']}")
            print(f"Citation: {repr(row['citation'])}")
            print(f"B candidate matched_title: {b_res.get('matched_title')}")
            print(f"B decision: 1 (exists={b_res.get('exists')}, title_score={b_res.get('title_similarity')}, author_score={b_res.get('author_similarity')})")
            print(f"C best candidate title: {c_res.get('best_candidate', {}).get('title')}")
            print(f"C title similarity score: {c_res.get('best_score')}")
            print(f"C decision: 0")
            print("-" * 60)
            
    print("\n=== EXAMPLES WHERE B=0 (Valid) and C=1 (Hallucinated) ===")
    
    for row in rows:
        if b0_c1_count >= 10:
            break
            
        cit = row["citation"]
        
        sys.stdout = DummyFile()
        b_pred, b_res = get_config_b_debug(cit)
        c_pred, c_res = get_config_c_debug(cit)
        sys.stdout = orig_stdout
        
        if b_pred == 0 and c_pred == 1:
            b0_c1_count += 1
            print(f"ID: {row['id']} | Error Type: {row['error_type']}")
            print(f"Citation: {repr(row['citation'])}")
            print(f"B candidate matched_title: {b_res.get('matched_title')}")
            print(f"B decision: 0 (exists={b_res.get('exists')}, title_score={b_res.get('title_similarity')}, author_score={b_res.get('author_similarity')})")
            print(f"C best candidate title: {c_res.get('best_candidate', {}).get('title')}")
            print(f"C title similarity score: {c_res.get('best_score')}")
            print(f"C decision: 1")
            print("-" * 60)

if __name__ == "__main__":
    main()
