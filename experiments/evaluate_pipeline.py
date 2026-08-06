import json
import csv
import sys
from pathlib import Path
from datetime import datetime

# Add the backend directory to sys.path so we can import the pipeline
BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"
sys.path.append(str(BACKEND_DIR))

from app.services.verification_pipeline import verify_response

def evaluate():
    dataset_path = BASE_DIR / "datasets" / "prompt_injection" / "test_set.json"
    
    if not dataset_path.exists():
        print(f"Error: Dataset not found at {dataset_path}")
        print("Please create this file with a list of test cases. Example format:")
        print('[{"id": 1, "llm_response": "...", "expected_hallucination": true}]')
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []
    
    print(f"Starting evaluation on {len(dataset)} items...")
    
    true_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0

    for item in dataset:
        print(f"Evaluating item {item.get('id', 'unknown')}...")
        
        # Run pipeline
        pipeline_results = verify_response(item["llm_response"])
        
        for idx, citation_result in enumerate(pipeline_results):
            # Evaluate hallucination detection
            is_hallucinated = citation_result["paper_exists"] == False or citation_result["citation_accurate"] == False
            expected_hallucination = item.get("expected_hallucination", True) # Default to true for testing if missing
            
            if is_hallucinated and expected_hallucination:
                true_positives += 1
            elif is_hallucinated and not expected_hallucination:
                false_positives += 1
            elif not is_hallucinated and not expected_hallucination:
                true_negatives += 1
            elif not is_hallucinated and expected_hallucination:
                false_negatives += 1
                
            results.append({
                "id": item.get("id", "unknown"),
                "citation_index": idx + 1,
                "extracted_citation": citation_result["citation"],
                "paper_exists": citation_result["paper_exists"],
                "hallucination_type": citation_result["hallucination_type"],
                "expected_hallucination": expected_hallucination,
                "is_hallucinated": is_hallucinated,
                "correct_prediction": is_hallucinated == expected_hallucination
            })

    # Calculate metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print("\n" + "="*40)
    print("EVALUATION RESULTS")
    print("="*40)
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print("="*40)

    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = BASE_DIR / "experiments" / f"evaluation_results_{timestamp}.csv"
    
    if results:
        keys = results[0].keys()
        with open(output_path, "w", newline="", encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(results)
            
        print(f"Results saved to {output_path}")

if __name__ == "__main__":
    evaluate()