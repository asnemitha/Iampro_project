import sys
import json
import logging
sys.path.insert(0, 'c:/Users/A S Nemitha/Desktop/CiteGuard/backend')

from app.services.verification_pipeline import verify_response
import app.services.citation_extractor as citation_extractor

valid_citation = """Title: "Editorial: Human and Machine Learning"
Authors: Pat Langley
Year: 1986
Venue: Machine Learning
DOI: 10.1023/a:1022854429410"""

hallucinated_citation = """Title: "Context Aware Verification of Automatically Generated Citations (91)"
Authors: David Wilson; Olivia Martin
Year: 2024
Venue: Information Processing and Management
DOI: 10.9999/citeguard.synthetic.0091"""

def run_diagnostic(name, citation):
    print(f"=== {name} CITATION ===")
    print(f"Input passed to verify_response():\n{citation}\n")
    
    # Manually check what the extractor sees
    extracted = citation_extractor.extract_citations(citation)
    print(f"Extracted citation results directly from extract_citations(): {extracted}")
    
    # Run through the pipeline
    raw_response = verify_response(citation)
    print(f"Raw response from verify_response(): {json.dumps(raw_response, indent=2)}")
    
    if raw_response:
        acc = raw_response[0].get("citation_accurate")
        print(f"citation_accurate: {acc}")
        pred = 0 if acc else 1
        print(f"Final prediction: {pred}")
    else:
        print("citation_accurate: N/A (list is empty)")
        print("Final prediction: 1 (Defaulted due to empty list)")
    print("-" * 60 + "\n")

if __name__ == "__main__":
    # Suppress verbose prints from pipeline
    class DummyFile(object):
        def write(self, x): pass
        def flush(self): pass
    orig_stdout = sys.stdout
    sys.stdout = DummyFile()
    
    # We will buffer our own prints
    output = []
    def log(msg):
        output.append(msg)
        
    def run_diagnostic_captured(name, citation):
        log(f"=== {name} CITATION ===")
        log(f"Input passed to verify_response():\n{citation}\n")
        
        extracted = citation_extractor.extract_citations(citation)
        log(f"Extracted citation results directly from extract_citations(): {extracted}")
        
        raw_response = verify_response(citation)
        log(f"Raw response from verify_response(): {json.dumps(raw_response, indent=2)}")
        
        if raw_response:
            acc = raw_response[0].get("citation_accurate")
            log(f"citation_accurate: {acc}")
            pred = 0 if acc else 1
            log(f"Final prediction: {pred}")
        else:
            log("citation_accurate: N/A (list is empty)")
            log("Final prediction: 1 (Defaulted due to empty list)")
        log("-" * 60 + "\n")

    run_diagnostic_captured("VALID", valid_citation)
    run_diagnostic_captured("HALLUCINATED", hallucinated_citation)
    
    sys.stdout = orig_stdout
    for msg in output:
        print(msg)
