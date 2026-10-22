import sys
import csv
import json
from collections import Counter
sys.path.insert(0, 'c:/Users/A S Nemitha/Desktop/CiteGuard/backend')

from app.services.verification_pipeline import verify_response
import app.services.citation_parser as citation_parser

detailed_path = 'c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification/ablation_detailed_results.csv'
dataset_path = 'c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification/hard_citation_test_dataset.csv'

# Suppress prints
class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

def main():
    fn_ids = []
    with open(detailed_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['configuration'] == 'Full CiteGuard' and row['ground_truth'] == '1' and row['prediction'] == '0':
                fn_ids.append(row['citation_id'])
                
    if len(fn_ids) != 94:
        print(f"Expected 94 FN, found {len(fn_ids)}")
        
    dataset = {}
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dataset[row['id']] = row

    results = []
    orig_stdout = sys.stdout
    
    for cid in fn_ids:
        row = dataset[cid]
        cit = row['citation']
        err_type = row['error_type']
        
        sys.stdout = DummyFile()
        llm_formatted_citation = f"[1]\n{cit}"
        raw = verify_response(llm_formatted_citation)
        sys.stdout = orig_stdout
        
        parsed = citation_parser.parse_citation(cit)
        has_doi = bool(parsed.get('doi'))
        
        if not raw:
            results.append({
                "id": cid, "error_type": err_type, "has_doi": has_doi, "raw": None
            })
            continue
            
        res = raw[0]
        results.append({
            "id": cid,
            "error_type": err_type,
            "has_doi": has_doi,
            "citation": cit,
            "raw": res
        })

    # Analysis
    error_counts = Counter([r['error_type'] for r in results])
    print(f"Total FN analyzed: {len(results)}")
    for err, count in error_counts.items():
        print(f"Error Type: {err} -> {count} ({(count/len(results))*100:.1f}%)")
        
    print("\n--- 20 Representative Examples ---")
    # Take up to 20 across different error types
    sampled = []
    seen_err = Counter()
    for r in results:
        if len(sampled) < 20 and r['raw']:
            sampled.append(r)
            seen_err[r['error_type']] += 1
            
    for i, r in enumerate(sampled):
        res = r['raw']
        print(f"\n[{i+1}] ID: {r['id']} | Error Type: {r['error_type']}")
        print(f"Has DOI: {r['has_doi']}")
        # The pipeline combines sources into candidates but verify_response returns the BEST candidate.
        print(f"Title Similarity: {res.get('title_similarity')}")
        print(f"Author Similarity: {res.get('author_similarity')}")
        print(f"Year Match: {res.get('year_match')}")
        print(f"Venue Match: {res.get('venue_match')}")
        print(f"DOI Match: {res.get('doi_match')}")
        print(f"Candidate Score: {res.get('candidate_score')}")
        print(f"Hallucination Score: {res.get('hallucination_score')}")
        print(f"Metadata Errors: {res.get('metadata_errors')}")

if __name__ == "__main__":
    main()
