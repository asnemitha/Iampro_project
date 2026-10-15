from app.services.multi_source_retriever import retrieve_candidates
from app.services.candidate_ranker import rank_candidates

from app.services.citation_extractor import extract_citations
from app.services.citation_parser import parse_citation
from app.services.citation_formatter import format_ieee
from app.services.prompt_consistency_service import check_prompt_consistency
from app.services.metadata_normalizer import canonicalize_verified_metadata

from app.services.crossref_service import (
    verify_doi,
)

from app.services.similarity_service import (
    compare_titles,
    compare_authors,
    compare_year,
    compare_venues,
    compare_dois,
    hallucination_score,
)

def _safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            print(str(text).encode("ascii", "replace").decode())
        except Exception:
            pass

def verify_response(llm_response: str, use_author_fix: bool = False, use_venue_fix: bool = False, user_prompt: str = None, venue_threshold: float = 70.0):
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
        _safe_print(citation)

        parsed = parse_citation(citation)

        print("\nPARSED METADATA")
        _safe_print(parsed)

        paper = None
        ranking_details = None

        # =====================================================
        # STEP 1
        # Verify DOI
        # =====================================================

        doi_paper = None
        if parsed["doi"]:

            print("\nSearching by DOI...")
            print(parsed["doi"])

            doi_paper = verify_doi(parsed["doi"])

            if doi_paper:

                print("\nDOI Candidate")
                print("-----------------------------")
                _safe_print(f"Title : {doi_paper.get('title')}")
                print("Source:", doi_paper.get("source", "Crossref"))

                # Check if DOI candidate matches title or is corroborated by authors and metadata
                if parsed["title"]:

                    title_similarity = compare_titles(
                        parsed["title"],
                        doi_paper["title"]
                    )["score"]

                    print(
                        "Title Similarity:",
                        round(title_similarity, 2)
                    )

                    author_sim = compare_authors(
                        parsed.get("authors"),
                        doi_paper.get("authors")
                    ) if (parsed.get("authors") and doi_paper.get("authors")) else 0.0

                    year_sim = compare_year(
                        parsed.get("year"),
                        doi_paper.get("year"),
                        doi_paper.get("alternate_years")
                    ) if parsed.get("year") else True

                    venue_match, _ = compare_venues(
                        parsed.get("venue"),
                        doi_paper.get("venue"),
                        use_venue_fix=use_venue_fix,
                        threshold=venue_threshold,
                    ) if parsed.get("venue") else (True, 100.0)

                    if title_similarity >= 75:
                        paper = doi_paper
                    elif author_sim >= 70 and (year_sim or venue_match) and title_similarity >= 40:
                        print(
                            "DOI corroborated by authors, metadata, and partial title match."
                        )
                        paper = doi_paper
                    else:
                        print(
                            "DOI belongs to another paper."
                        )
                        paper = None
                else:
                    paper = doi_paper

        # =====================================================
        # STEP 2
        # Multi-Source Retrieval
        # =====================================================

        if paper is None and parsed["title"]:

            print("\nSearching Multiple Sources...")

            candidates = retrieve_candidates(
                parsed["title"],
                authors=parsed.get("authors"),
                year=parsed.get("year"),
                doi=parsed.get("doi"),
            )

            # Include doi_paper in candidates pool if verified and not already present
            if doi_paper and not any(compare_dois(c.get("doi"), doi_paper.get("doi")) for c in candidates):
                candidates.append(doi_paper)

            print(
                "Retrieved Candidates:",
                len(candidates)
            )

            for candidate in candidates[:5]:
                print("----------------------------")
                _safe_print(candidate.get("title"))
                print(
                    "Source:",
                    candidate.get("source", "Unknown")
                )

            import re
            prefers_original = False
            if user_prompt:
                prefers_original = bool(
                    re.search(r"\boriginal\s+(?:paper|publication|work|version|article)\b", user_prompt, re.IGNORECASE)
                )

            ranked = rank_candidates(
                parsed,
                candidates,
                use_venue_fix=use_venue_fix,
                prefers_original=prefers_original,
                venue_threshold=venue_threshold,
            )

            if ranked:
                cand_title_score = ranked[0]["title_score"]
                cand_author_score = ranked[0]["author_score"]
                cand_year_match = ranked[0]["year_score"] == 100
                cand_venue_match = ranked[0]["venue_score"] >= 80
                cand_doi_match = ranked[0]["doi_score"] == 100
                top_cand = ranked[0]["paper"]
                cand_has_authors = bool(top_cand.get("authors") and len(top_cand["authors"]) > 0)
                parsed_has_authors = bool(parsed.get("authors") and len(parsed["authors"]) > 0)

                is_candidate_viable = (
                    (cand_title_score >= 80 and (not parsed_has_authors or cand_has_authors or cand_doi_match))
                    or (cand_title_score >= 70 and cand_author_score >= 60 and (cand_year_match or cand_venue_match))
                    or (cand_author_score >= 60 and cand_doi_match)
                    or (cand_doi_match and (cand_year_match or cand_venue_match))
                )
                if is_candidate_viable:
                    ranking_details = ranked[0]
                    paper = ranking_details["paper"]
                    print("\nBEST MATCH")
                    print("----------------------------")
                    _safe_print(paper.get("title"))
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
                    ranking_details = None
                    print(
                        "\nCandidate does not meet existence criteria."
                    )
            else:
                paper = None
                ranking_details = None
                print(
                    "\nNo suitable paper found."
                )

        # Fallback to verified DOI paper if multi-source retrieval did not find a paper
        # (DOI-first verification: DOI resolved to an authoritative scholarly paper, but title was hallucinated/mismatched)
        if paper is None and doi_paper is not None:
            paper = doi_paper
            print("\nRetained verified paper from authoritative DOI lookup.")

        # =====================================================
        # STEP 3
        # No Paper Found
        # =====================================================

        if paper is None:

            print("\nNO MATCH FOUND")
            print("=" * 80)

            prompt_consistency = (
                check_prompt_consistency(user_prompt, parsed, matched_paper=None)
                if user_prompt
                else None
            )

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

                "confidence": "High Risk of Hallucination",

                "corrected_citation": None,

                "reason": ["Paper could not be verified in scholarly databases."],

                "prompt_consistency": prompt_consistency,

            })

            continue

        # =====================================================
        # STEP 4
        # Similarity Calculation
        # =====================================================

        title = compare_titles(
            parsed["title"],
            paper.get("title")
        )

        author_score = compare_authors(
            parsed.get("authors"),
            paper.get("authors")
        )

        year_match = compare_year(
            parsed.get("year"),
            paper.get("year"),
            paper.get("alternate_years")
        )

        venue_match, venue_sim = compare_venues(
            parsed.get("venue"),
            paper.get("venue"),
            use_venue_fix=use_venue_fix,
            threshold=venue_threshold,
        )

        doi_match = compare_dois(
            parsed.get("doi"),
            paper.get("doi")
        )

        if ranking_details:
            overall_score = ranking_details["final_score"]
        else:
            overall_score = (
                title["score"] * 0.40 +
                author_score * 0.25 +
                (100 if year_match else 0) * 0.15 +
                (venue_sim if venue_match else 0) * 0.10 +
                (100 if doi_match else 0) * 0.10
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
            or (title["score"] >= 70 and author_score >= 60 and (year_match or venue_match))
            or doi_match
        )

        # =====================================================
        # STEP 7
        # Citation Accuracy
        # =====================================================

        title_check = title["score"] >= 80
        if use_author_fix:
            author_check = (author_score >= 70) if (parsed.get("authors") and len(parsed["authors"]) > 0) else True
        else:
            author_check = True
        year_check = year_match if parsed.get("year") else True
        venue_check = venue_match if parsed.get("venue") else True

        if parsed.get("doi"):
            if doi_match:
                doi_check = True
            elif str(parsed["doi"]).strip().lower().replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "").startswith("10.5555/"):
                target_venue = str(paper.get("venue") or parsed.get("venue") or "").lower()
                doi_check = any(v in target_venue for v in ["nips", "neurips", "acm"])
            elif not paper.get("doi"):
                # If the supplied DOI actually resolved to a completely different paper in Crossref, it is a DOI mismatch
                if doi_paper and compare_titles(parsed.get("title"), doi_paper.get("title"))["score"] < 70 and compare_authors(parsed.get("authors"), doi_paper.get("authors")) < 60:
                    doi_check = False
                else:
                    doi_check = True
            else:
                doi_check = False
        else:
            doi_check = True

        citation_accurate = (
            paper_exists
            and title_check
            and author_check
            and year_check
            and venue_check
            and doi_check
        )

        # =====================================================
        # STEP 8
        # Metadata Errors
        # =====================================================

        metadata_errors = []

        if parsed.get("title") and not title_check:
            metadata_errors.append("Paper title mismatch")

        if parsed.get("authors") and author_score < 70:
            metadata_errors.append("Author mismatch")

        if parsed.get("year") and not year_check:
            metadata_errors.append("Publication year mismatch")

        if parsed.get("venue") and not venue_check:
            metadata_errors.append("Venue mismatch")

        if parsed.get("doi") and not doi_check:
            metadata_errors.append("DOI mismatch")

        # =====================================================
        # STEP 9
        # Hallucination Type
        # =====================================================

        if not paper_exists:
            hallucination_type = "Fabricated Citation"
        elif citation_accurate:
            hallucination_type = "Valid Citation"
        else:
            hallucination_type = "Metadata Hallucination"

        # =====================================================
        # STEP 10
        # Hallucination Score
        # =====================================================

        if citation_accurate:
            score = 0
        elif not paper_exists:
            score = 100
        else:
            score = hallucination_score(
                title_score=title["score"],
                author_score=author_score,
                year_match=year_match,
                doi_match=doi_check,
                venue_match=venue_match,
                doi_provided=bool(parsed.get("doi")),
                venue_provided=bool(parsed.get("venue")),
                year_provided=bool(parsed.get("year")),
                citation_accurate=citation_accurate,
            )

        # =====================================================
        # STEP 11
        # Confidence
        # =====================================================

        if citation_accurate:
            confidence = "Verified Citation"
        elif paper_exists:
            confidence = "Paper Exists but Citation Contains Errors"
        else:
            confidence = "High Risk of Hallucination"

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
        # (ONLY for inaccurate citations where paper exists)
        # =====================================================

        canonical_meta = canonicalize_verified_metadata(paper, parsed_citation=parsed)
        corrected = None

        if not citation_accurate and paper_exists:
            corrected = format_ieee(canonical_meta)

        # =====================================================
        # STEP 13
        # Build Human Readable Reasons & Prompt Consistency
        # =====================================================

        prompt_consistency = (
            check_prompt_consistency(user_prompt, parsed, matched_paper=paper)
            if user_prompt
            else None
        )

        reasons = []

        if paper_exists:
            reasons.append("Paper found in scholarly databases.")
        else:
            reasons.append("Paper could not be verified.")

        if parsed.get("title"):
            if title_check:
                reasons.append("Paper title matches.")
            else:
                reasons.append("Paper title differs.")

        if parsed.get("authors"):
            if author_score >= 70:
                if prompt_consistency and not prompt_consistency.get("matches", True) and "authors" in prompt_consistency.get("mismatched_fields", []):
                    reasons.append("Authors match scholarly database record (note: differs from authors requested in prompt).")
                else:
                    reasons.append("Authors match.")
            else:
                reasons.append("Authors differ.")

        if parsed.get("year"):
            if year_check:
                reasons.append("Publication year matches.")
            else:
                reasons.append("Publication year differs.")

        if parsed.get("doi"):
            if doi_check:
                reasons.append("DOI verified.")
            else:
                reasons.append("DOI differs.")

        if parsed.get("venue"):
            if venue_check:
                reasons.append("Venue matches.")
            else:
                reasons.append("Venue differs.")

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

            "matched_title": canonical_meta.get("title") or paper.get("title"),

            "matched_authors": canonical_meta.get("authors") or paper.get("authors"),

            "matched_year": canonical_meta.get("year") or paper.get("year"),

            "matched_venue": canonical_meta.get("venue") or paper.get("venue"),

            "matched_doi": canonical_meta.get("doi") or paper.get("doi"),

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

            "prompt_consistency": prompt_consistency,

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