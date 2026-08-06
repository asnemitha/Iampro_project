from app.services.multi_source_retriever import retrieve_candidates
from app.services.candidate_ranker import rank_candidates

from app.services.citation_extractor import extract_citations
from app.services.citation_parser import parse_citation
from app.services.citation_formatter import format_ieee

from app.services.crossref_service import (
    verify_doi,
)

from app.services.similarity_service import (
    compare_titles,
    compare_authors,
    compare_year,
    hallucination_score,
)


def verify_response(llm_response: str):
    """
    Main citation verification pipeline.

    Pipeline

    LLM Response
            ↓
    Citation Extraction
            ↓
    Citation Parsing
            ↓
    DOI Verification
            ↓
    Multi-Source Retrieval
            ↓
    Candidate Ranking
            ↓
    Metadata Verification
            ↓
    Hallucination Diagnosis
    """

    citations = extract_citations(llm_response)

    results = []

    print("\n")
    print("=" * 80)
    print("CITATIONS FOUND:", len(citations))
    print("=" * 80)

    for index, citation in enumerate(citations, start=1):

        print("\n")
        print("=" * 80)
        print(f"CITATION {index}")
        print("=" * 80)
        print(citation)

        parsed = parse_citation(citation)

        print("\nPARSED METADATA")
        print(parsed)

        paper = None
        ranking_details = None

                # =====================================================
        # STEP 1
        # Verify DOI
        # =====================================================

        if parsed["doi"]:

            print("\nSearching by DOI...")
            print(parsed["doi"])

            paper = verify_doi(parsed["doi"])

            if paper:

                print("\nDOI Candidate")
                print("-----------------------------")
                print("Title :", paper["title"])
                print("Source: Crossref")

                # Reject incorrect DOI if title does not match
                if parsed["title"]:

                    title_similarity = compare_titles(
                        parsed["title"],
                        paper["title"]
                    )["score"]

                    print(
                        "Title Similarity:",
                        round(title_similarity, 2)
                    )

                    if title_similarity < 90:

                        print(
                            "DOI belongs to another paper."
                        )

                        paper = None

        # =====================================================
        # STEP 2
        # Multi-Source Retrieval
        # =====================================================

        if paper is None and parsed["title"]:

            print("\nSearching Multiple Sources...")

            candidates = retrieve_candidates(
                parsed["title"]
            )

            print(
                "Retrieved Candidates:",
                len(candidates)
            )

            for candidate in candidates[:5]:

                print("----------------------------")

                print(
                    candidate.get("title")
                )

                print(
                    "Source:",
                    candidate.get(
                        "source",
                        "Unknown"
                    )
                )

            ranked = rank_candidates(
                parsed,
                candidates
            )

            if ranked:

                ranking_details = ranked[0]

                paper = ranking_details["paper"]

                print("\nBEST MATCH")
                print("----------------------------")
                print(
                    paper["title"]
                )

                print(
                    "Source:",
                    paper.get(
                        "source",
                        "Unknown"
                    )
                )

                print(
                    "Ranking Score:",
                    ranking_details[
                        "final_score"
                    ]
                )

            else:

                paper = None

                print(
                    "\nNo suitable paper found."
                )

                    # =====================================================
        # STEP 3
        # No Paper Found
        # =====================================================

        if paper is None:

            print("\nNO MATCH FOUND")
            print("=" * 80)

            results.append({

                "citation": citation,

                "paper_exists": False,

                "citation_accurate": False,

                "hallucination_type": "Fabricated Citation",

                "metadata_errors": [
                    "Paper could not be found in Crossref, Semantic Scholar or OpenAlex."
                ],

                "matched_title": None,

                "matched_authors": [],

                "matched_year": None,

                "matched_venue": None,

                "matched_doi": None,

                "candidate_score": 0,

                "title_similarity": 0,

                "author_similarity": 0,

                "year_match": False,

                "venue_match": False,

                "doi_match": False,

                "hallucination_score": 100,

                "confidence": "Citation Not Verified",

                "corrected_citation": None,

            })

            continue

        # =====================================================
        # STEP 4
        # Similarity Calculation
        # =====================================================

        if ranking_details:

            title = {

                "score": ranking_details["title_score"]

            }

            author_score = ranking_details["author_score"]

            year_match = (

                ranking_details["year_score"] == 100

            )

            venue_match = (

                ranking_details["venue_score"] >= 80

            )

            overall_score = ranking_details["final_score"]

        else:

            title = compare_titles(

                parsed["title"],

                paper["title"]

            )

            author_score = compare_authors(

                parsed["authors"],

                paper["authors"]

            )

            year_match = compare_year(

                parsed["year"],

                paper["year"]

            )

            venue_match = False

            if parsed["venue"] and paper["venue"]:

                venue_match = (

                    parsed["venue"].strip().lower()

                    ==

                    paper["venue"].strip().lower()

                )

            overall_score = (

                title["score"] * 0.40 +

                author_score * 0.20 +

                (100 if year_match else 0) * 0.10 +

                (100 if venue_match else 0) * 0.10

            )

        # =====================================================
        # STEP 5
        # DOI Match
        # =====================================================

        doi_match = False

        if parsed["doi"] and paper["doi"]:

            doi_match = (

                parsed["doi"].strip().lower()

                ==

                paper["doi"].strip().lower()

            )

        print("\nVERIFICATION")
        print("-----------------------------")

        print(
            "Title Similarity :",
            round(title["score"], 2)
        )

        print(
            "Author Similarity:",
            round(author_score, 2)
        )

        print(
            "Year Match       :",
            year_match
        )

        print(
            "Venue Match      :",
            venue_match
        )

        print(
            "DOI Match        :",
            doi_match
        )

        print(
            "Overall Score    :",
            round(overall_score, 2)
        )

                # =====================================================
        # STEP 6
        # Paper Existence
        # =====================================================

        paper_exists = (
            title["score"] >= 80
            or
            (title["score"] >= 70 and author_score >= 40)
            or
            doi_match
        )

        # =====================================================
        # STEP 7
        # Citation Accuracy
        # =====================================================

        citation_accurate = (
            paper_exists
            and
            (doi_match if parsed["doi"] else True)
            and
            year_match
            and
            venue_match
        )

        # =====================================================
        # STEP 8
        # Metadata Errors
        # =====================================================

        metadata_errors = []

        if title["score"] < 92:

            metadata_errors.append(
                "Paper title mismatch"
            )

        if author_score < 70:

            metadata_errors.append(
                "Author mismatch"
            )

        if not year_match:

            metadata_errors.append(
                "Publication year mismatch"
            )

        if not venue_match:

            metadata_errors.append(
                "Venue mismatch"
            )

        if parsed["doi"]:

            if not doi_match:

                metadata_errors.append(
                    "DOI mismatch"
                )

        # =====================================================
        # STEP 9
        # Hallucination Type
        # =====================================================

        if not paper_exists:

            hallucination_type = (
                "Fabricated Citation"
            )

        elif citation_accurate:

            hallucination_type = (
                "Verified Citation"
            )

        else:

            hallucination_type = (
                "Metadata Hallucination"
            )

        # =====================================================
        # STEP 10
        # Hallucination Score
        # =====================================================

        score = hallucination_score(

            title_score=title["score"],

            author_score=author_score,

            year_match=year_match,

            doi_match=doi_match,

            venue_match=venue_match,

        )

        # =====================================================
        # STEP 11
        # Confidence
        # =====================================================

        if citation_accurate:

            confidence = (
                "Verified Citation"
            )

        elif paper_exists:

            confidence = (
                "Paper Exists but Citation Contains Errors"
            )

        else:

            confidence = (
                "High Risk of Hallucination"
            )

        print("\nFINAL RESULT")
        print("----------------------------")

        print(
            "Paper Exists      :",
            paper_exists
        )

        print(
            "Citation Accurate :",
            citation_accurate
        )

        print(
            "Hallucination     :",
            hallucination_type
        )

        print(
            "Confidence        :",
            confidence
        )

        print(
            "HallucinationScore:",
            score
        )

        print("=" * 80)

                # =====================================================
        # STEP 12
        # Generate Corrected Citation
        # =====================================================

        corrected = None

        if not citation_accurate and paper_exists:

            corrected = format_ieee(paper)

        # =====================================================
        # STEP 13
        # Build Human Readable Reasons
        # =====================================================

        reasons = []

        if paper_exists:

            reasons.append(
                "Paper found in scholarly databases."
            )

        else:

            reasons.append(
                "Paper could not be verified."
            )

        if title["score"] >= 92:

            reasons.append(
                "Paper title matches."
            )

        else:

            reasons.append(
                "Paper title differs."
            )

        if author_score >= 70:

            reasons.append(
                "Authors match."
            )

        else:

            reasons.append(
                "Authors differ."
            )

        if year_match:

            reasons.append(
                "Publication year matches."
            )

        else:

            reasons.append(
                "Publication year differs."
            )

        if parsed["doi"]:

            if doi_match:

                reasons.append(
                    "DOI verified."
                )

            else:

                reasons.append(
                    "DOI differs."
                )

        if venue_match:

            reasons.append(
                "Venue matches."
            )

        else:

            reasons.append(
                "Venue differs."
            )

        # =====================================================
        # STEP 14
        # Store Result
        # =====================================================

        results.append({

            "citation": citation,

            "paper_exists": paper_exists,

            "citation_accurate": citation_accurate,

            "hallucination_type": hallucination_type,

            "confidence": confidence,

            "reason": reasons,

            "metadata_errors": metadata_errors,

            "matched_title": paper.get("title"),

            "matched_authors": paper.get("authors"),

            "matched_year": paper.get("year"),

            "matched_venue": paper.get("venue"),

            "matched_doi": paper.get("doi"),

            "candidate_score": round(
                overall_score,
                2
            ),

            "title_similarity": round(
                title["score"],
                2
            ),

            "author_similarity": round(
                author_score,
                2
            ),

            "year_match": year_match,

            "venue_match": venue_match,

            "doi_match": doi_match,

            "hallucination_score": score,

            "corrected_citation": corrected,

        })

            # =====================================================
    # Verification Completed
    # =====================================================

    print("\n")
    print("=" * 80)
    print("VERIFICATION COMPLETED")
    print("Total Citations Processed:", len(results))
    print("=" * 80)

    return results