import csv
import json
import sys
import os
from pathlib import Path
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Suppress prints from the pipeline
class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

# We will redirect stdout during the heavy calls so it doesn't spam the terminal
sys.stdout = DummyFile()

import app.services.citation_parser as citation_parser
import app.services.crossref_service as crossref_service
import app.services.citation_verifier as citation_verifier
import app.services.similarity_service as similarity_service
import app.services.verification_pipeline as verification_pipeline

sys.stdout = sys.__stdout__

DATASET_FILE = Path(__file__).resolve().parent / "hard_citation_test_dataset.csv"
RESULTS_FILE = Path(__file__).resolve().parent / "ablation_results.csv"
DETAILED_RESULTS_FILE = Path(__file__).resolve().parent / "ablation_detailed_results.csv"
SUMMARY_FILE = Path(__file__).resolve().parent / "ablation_summary.json"


def eval_config_a(citation):
    try:
        parsed = citation_parser.parse_citation(citation)
        doi = parsed.get("doi")
        if doi:
            result = crossref_service.verify_doi(doi)
            if result:
                return 0
        return 1
    except Exception as e:
        return 1

def eval_config_b(citation):
    try:
        result = citation_verifier.verify_citation(citation)
        if result.get("exists", False):
            return 0
        return 1
    except Exception as e:
        return 1

def eval_config_c(citation):
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
            return 1
            
        best_title_score = 0
        for candidate in candidates:
            cand_title = candidate.get("title")
            if not cand_title: continue
            
            sim_res = similarity_service.compare_titles(title, cand_title)
            score = sim_res.get("score", 0)
            if score > best_title_score:
                best_title_score = score
                
        if best_title_score >= 80:
            return 0
        return 1
    except Exception as e:
        return 1

def normalize_doi(doi):
    if not doi: return ""
    return doi.replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "").strip().lower()

def eval_config_d(citation):
    try:
        parsed = citation_parser.parse_citation(citation)
        doi = parsed.get("doi")
        title = parsed.get("title")
        authors = parsed.get("authors", [])
        year = parsed.get("year")
        venue = parsed.get("venue")
        
        candidates = []
        if doi:
            res = crossref_service.verify_doi(doi)
            if res: candidates.append(res)
        if title:
            title_res = crossref_service.verify_title(title, rows=5)
            if title_res:
                candidates.extend(title_res)
                
        if not candidates:
            return 1
            
        is_valid = False
        for candidate in candidates:
            cand_title = candidate.get("title", "")
            cand_authors = candidate.get("authors", [])
            cand_year = candidate.get("year")
            cand_venue = candidate.get("venue", "")
            cand_doi = candidate.get("doi", "")
            
            title_sim = similarity_service.compare_titles(title, cand_title)
            title_score = title_sim.get("score", 0)
            
            author_score = similarity_service.compare_authors(authors, cand_authors)
            
            doi_match = False
            if doi and cand_doi:
                doi_match = (normalize_doi(doi) == normalize_doi(cand_doi))
                
            year_match = similarity_service.compare_year(year, cand_year)
            
            venue_match = False
            if venue and cand_venue:
                venue_match = (venue.strip().lower() == cand_venue.strip().lower())
                
            # Logic from verification_pipeline.py
            paper_exists = (
                title_score >= 80
                or
                (title_score >= 70 and author_score >= 40)
                or
                doi_match
            )
            
            citation_accurate = (
                paper_exists
                and
                (doi_match if doi else True)
                and
                (year_match if year else True)
                and
                (venue_match if venue else True)
            )
            
            if citation_accurate:
                is_valid = True
                break
                
        if is_valid:
            return 0
        return 1
        
    except Exception as e:
        return 1

def eval_config_e(citation):
    try:
        llm_formatted_citation = f"[1]\n{citation}"
        results = verification_pipeline.verify_response(llm_formatted_citation)
        if not results:
            return 1
        result = results[0]
        if result.get("citation_accurate", False):
            return 0
        return 1
    except Exception as e:
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
        reader = csv.DictReader(f)
        rows = list(reader)
        
    print(f"Loaded {len(rows)} citations.")
    
    detailed_results = []
    
    y_true = []
    y_pred_A = []
    y_pred_B = []
    y_pred_C = []
    y_pred_D = []
    y_pred_E = []
    
    print("Running evaluations. This may take a while as APIs are queried...")
    for idx, row in enumerate(rows, start=1):
        if idx % 10 == 0:
            print(f"Processing row {idx}/{len(rows)}")
            
        citation = row["citation"]
        ground_truth = int(row["ground_truth"])
        y_true.append(ground_truth)
        
        sys.stdout = DummyFile() # block spam
        pred_a = eval_config_a(citation)
        pred_b = eval_config_b(citation)
        pred_c = eval_config_c(citation)
        pred_d = eval_config_d(citation)
        pred_e = eval_config_e(citation)
        sys.stdout = sys.__stdout__
        
        y_pred_A.append(pred_a)
        y_pred_B.append(pred_b)
        y_pred_C.append(pred_c)
        y_pred_D.append(pred_d)
        y_pred_E.append(pred_e)
        
        for config_name, pred in [("DOI-only", pred_a), 
                                  ("Crossref Metadata", pred_b), 
                                  ("Crossref + Title", pred_c), 
                                  ("Crossref + Title + Authors + Year + Venue", pred_d), 
                                  ("Full CiteGuard", pred_e)]:
            detailed_results.append({
                "citation_id": row["id"],
                "error_type": row["error_type"],
                "ground_truth": ground_truth,
                "prediction": pred,
                "configuration": config_name
            })
            
    # Save detailed results
    with open(DETAILED_RESULTS_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["citation_id", "error_type", "ground_truth", "prediction", "configuration"])
        writer.writeheader()
        writer.writerows(detailed_results)
        
    # Compute overall metrics
    configs = [
        ("DOI-only", y_pred_A),
        ("Crossref Metadata", y_pred_B),
        ("Crossref + Title", y_pred_C),
        ("Crossref + Title + Authors + Year + Venue", y_pred_D),
        ("Full CiteGuard", y_pred_E)
    ]
    
    results = []
    summary = {}
    
    for config_name, y_pred in configs:
        metrics = calculate_metrics(y_true, y_pred)
        results.append({
            "configuration": config_name,
            **metrics
        })
        
        error_types = set(r["error_type"] for r in rows)
        error_metrics = {}
        for etype in error_types:
            y_t = [int(rows[i]["ground_truth"]) for i in range(len(rows)) if rows[i]["error_type"] == etype]
            y_p = [y_pred[i] for i in range(len(rows)) if rows[i]["error_type"] == etype]
            error_metrics[etype] = calculate_metrics(y_t, y_p)
            
        summary[config_name] = {
            "overall": metrics,
            "error_types": error_metrics
        }
        
    # Save overall results CSV
    with open(RESULTS_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["configuration", "total", "tp", "tn", "fp", "fn", "accuracy", "precision", "recall", "f1"])
        writer.writeheader()
        writer.writerows(results)
        
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
        
    print("Evaluations complete. Results saved.")
    
if __name__ == "__main__":
    main()
