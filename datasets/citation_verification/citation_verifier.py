from app.services.candidate_ranker import rank_candidates
from app.services.citation_extractor import extract_citations
from app.services.citation_parser import parse_citation
from app.services.citation_formatter import format_ieee

from app.services.crossref_service import (
    verify_doi,
    verify_title,
)

from app.services.similarity_service import (
    compare_titles,
    compare_authors,
    compare_year,
    hallucination_score,
)

from app.services.metadata_normalizer import (
    normalize_metadata,
)


# ============================================================
# THRESHOLDS
# ============================================================

TITLE_MATCH_THRESHOLD = 90
AUTHOR_MATCH_THRESHOLD = 70
EXACT_TITLE_THRESHOLD = 95

# A candidate below this score should NOT be treated
# as the requested paper.
MIN_CANDIDATE_SCORE = 75


# ============================================================
# VENUE SIMILARITY
# ============================================================

def venue_similarity(v1, v2):

    if not v1 or not v2:
        return 0.0

    v1 = str(v1).lower().strip()
    v2 = str(v2).lower().strip()

    if not v1 or not v2:
        return 0.0

    if v1 == v2:
        return 100.0

    if v1 in v2 or v2 in v1:
        return 90.0

    words1 = set(v1.split())
    words2 = set(v2.split())

    if not words1 or not words2:
        return 0.0

    overlap = len(words1 & words2)
    union = len(words1 | words2)

    if union == 0:
        return 0.0

    return (overlap / union) * 100.0


# ============================================================
# DOI NORMALIZATION
# ============================================================

def normalize_doi_value(doi):

    if not doi:
        return None

    doi = str(doi).strip()

    doi = doi.replace(
        "https://doi.org/",
        ""
    )

    doi = doi.replace(
        "http://doi.org/",
        ""
    )

    doi = doi.replace(
        "doi:",
        ""
    )

    return doi.strip().lower()


# ============================================================
# SAFE YEAR COMPARISON
# ============================================================

def safe_year_match(parsed_year, paper_year):

    if not parsed_year or not paper_year:
        return False

    try:
        return int(parsed_year) == int(paper_year)

    except (
        ValueError,
        TypeError,
    ):
        return False


# ============================================================
# VERIFY DOI AGAINST METADATA
# ============================================================

def verify_doi_match(
    parsed,
    paper,
):

    if not parsed:
        return False

    if not paper:
        return False

    parsed_doi = normalize_doi_value(
        parsed.get("doi")
    )

    paper_doi = normalize_doi_value(
        paper.get("doi")
    )

    if not parsed_doi or not paper_doi:
        return False

    return parsed_doi == paper_doi


# ============================================================
# VERIFY METADATA
# ============================================================

def calculate_verification(
    parsed,
    paper,
):

    parsed_title = parsed.get(
        "title"
    )

    parsed_authors = parsed.get(
        "authors",
        []
    )

    parsed_year = parsed.get(
        "year"
    )

    parsed_venue = parsed.get(
        "venue"
    )

    paper_title = paper.get(
        "title"
    )

    paper_authors = paper.get(
        "authors",
        []
    )

    paper_year = paper.get(
        "year"
    )

    paper_venue = paper.get(
        "venue"
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    if parsed_title and paper_title:

        title_result = compare_titles(
            parsed_title,
            paper_title
        )

        title_score = float(
            title_result.get(
                "score",
                0
            )
        )

    else:

        title_score = 0.0

    # --------------------------------------------------------
    # AUTHORS
    # --------------------------------------------------------

    if parsed_authors and paper_authors:

        author_score = float(
            compare_authors(
                parsed_authors,
                paper_authors,
            )
        )

    else:

        author_score = 0.0

    # --------------------------------------------------------
    # YEAR
    # --------------------------------------------------------

    year_match = safe_year_match(
        parsed_year,
        paper_year,
    )

    # --------------------------------------------------------
    # DOI
    # --------------------------------------------------------

    doi_match = verify_doi_match(
        parsed,
        paper,
    )

    # --------------------------------------------------------
    # VENUE
    # --------------------------------------------------------

    venue_match = False
    venue_score = 0.0

    if parsed_venue and paper_venue:

        venue_score = venue_similarity(
            parsed_venue,
            paper_venue,
        )

        venue_match = (
            venue_score >= 85
        )

    # --------------------------------------------------------
    # HALLUCINATION SCORE
    # --------------------------------------------------------

    score = hallucination_score(
        title_score=title_score,
        author_score=author_score,
        year_match=year_match,
        doi_match=doi_match,
        venue_match=venue_match,
    )

    return {
        "title_score": round(
            title_score,
            2,
        ),
        "author_score": round(
            author_score,
            2,
        ),
        "year_match": year_match,
        "doi_match": doi_match,
        "venue_match": venue_match,
        "venue_score": round(
            venue_score,
            2,
        ),
        "hallucination_score": score,
    }


# ============================================================
# DETERMINE WHETHER CITATION IS CORRECT
# ============================================================

def determine_existence(
    verification,
):

    title_score = verification[
        "title_score"
    ]

    author_score = verification[
        "author_score"
    ]

    year_match = verification[
        "year_match"
    ]

    doi_match = verification[
        "doi_match"
    ]

    # --------------------------------------------------------
    # STRONG DOI + TITLE CONFIRMATION
    # --------------------------------------------------------

    if doi_match and title_score >= TITLE_MATCH_THRESHOLD:

        return True

    # --------------------------------------------------------
    # STRONG METADATA MATCH
    # --------------------------------------------------------

    if (
        title_score >= EXACT_TITLE_THRESHOLD
        and
        author_score >= AUTHOR_MATCH_THRESHOLD
        and
        year_match
    ):

        return True

    return False


# ============================================================
# CLASSIFY RESULT
# ============================================================

def classify_result(
    exists,
    verification,
):

    score = verification[
        "hallucination_score"
    ]

    title_score = verification[
        "title_score"
    ]

    author_score = verification[
        "author_score"
    ]

    year_match = verification[
        "year_match"
    ]

    doi_match = verification[
        "doi_match"
    ]

    if exists:

        # Correctly verified paper,
        # but metadata may contain an error.

        if (
            doi_match
            and
            title_score >= TITLE_MATCH_THRESHOLD
        ):

            return (
                "Verified Citation"
            )

        return (
            "Paper Exists but "
            "Citation Contains Errors"
        )

    if score >= 80:

        return (
            "High Risk of Hallucination"
        )

    if score >= 50:

        return (
            "Possible Match"
        )

    return (
        "Citation Not Verified"
    )


# ============================================================
# GENERATE REASONS
# ============================================================

def generate_reasons(
    verification,
    exists,
):

    reasons = []

    title_score = verification[
        "title_score"
    ]

    author_score = verification[
        "author_score"
    ]

    year_match = verification[
        "year_match"
    ]

    doi_match = verification[
        "doi_match"
    ]

    venue_match = verification[
        "venue_match"
    ]

    if title_score >= 95:

        reasons.append(
            "Paper title matches the "
            "verified scholarly record."
        )

    elif title_score >= 80:

        reasons.append(
            "Paper title is highly similar "
            "to the verified record."
        )

    elif title_score >= 60:

        reasons.append(
            "Paper title is partially "
            "similar to the verified record."
        )

    else:

        reasons.append(
            "Paper title differs "
            "significantly."
        )

    if author_score >= 90:

        reasons.append(
            "Authors closely match."
        )

    elif author_score >= 70:

        reasons.append(
            "Most authors appear to match."
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

    if doi_match:

        reasons.append(
            "DOI matches the verified "
            "scholarly record."
        )

    else:

        reasons.append(
            "DOI does not match."
        )

    if venue_match:

        reasons.append(
            "Publication venue matches."
        )

    else:

        reasons.append(
            "Publication venue differs."
        )

    if exists:

        reasons.append(
            "A corresponding scholarly "
            "record was found."
        )

    else:

        reasons.append(
            "The citation could not be "
            "confirmed as the requested paper."
        )

    return reasons


# ============================================================
# VERIFY ONE CITATION
# ============================================================

def verify_single_citation(
    citation,
):

    parsed = parse_citation(
        citation
    )

    print()
    print("=" * 80)
    print("PARSED METADATA")
    print("=" * 80)

    print(parsed)

    paper = None
    ranking_details = None

    # ========================================================
    # STEP 1 — DOI SEARCH
    # ========================================================

    if parsed.get("doi"):

        print()
        print(
            "Searching by DOI..."
        )

        print(
            parsed["doi"]
        )

        try:

            doi_paper = verify_doi(
                parsed["doi"]
            )

        except Exception as exc:

            print(
                "DOI verification error:",
                exc
            )

            doi_paper = None

        if doi_paper:

            # Normalize Crossref metadata
            try:

                doi_paper = normalize_metadata(
                    doi_paper
                )

            except Exception:

                pass

            # ------------------------------------------------
            # IMPORTANT:
            # DOI alone is NOT enough.
            # Check title too.
            # ------------------------------------------------

            if parsed.get("title"):

                title_check = compare_titles(
                    parsed["title"],
                    doi_paper.get(
                        "title",
                        ""
                    ),
                )

                doi_title_score = float(
                    title_check.get(
                        "score",
                        0
                    )
                )

                print(
                    "DOI title similarity:",
                    round(
                        doi_title_score,
                        2
                    )
                )

                if (
                    doi_title_score
                    >= TITLE_MATCH_THRESHOLD
                ):

                    paper = doi_paper

                    print(
                        "DOI VERIFIED"
                    )

                else:

                    print(
                        "DOI found, but "
                        "title does not match."
                    )

            else:

                paper = doi_paper

                print(
                    "DOI VERIFIED"
                )

    # ========================================================
    # STEP 2 — TITLE SEARCH
    # ========================================================

    if paper is None and parsed.get(
        "title"
    ):

        print()
        print(
            "Searching by Title..."
        )

        try:

            candidates = verify_title(
                parsed["title"]
            )

        except Exception as exc:

            print(
                "Title search error:",
                exc
            )

            candidates = []

        if candidates:

            ranked = rank_candidates(
                parsed,
                candidates,
            )

            if ranked:

                best = ranked[0]

                candidate_score = float(
                    best.get(
                        "final_score",
                        0
                    )
                )

                print()
                print(
                    "BEST MATCH"
                )

                print(
                    "-" * 50
                )

                print(
                    "Title:",
                    best["paper"].get(
                        "title"
                    )
                )

                print(
                    "Score:",
                    candidate_score
                )

                # ------------------------------------------------
                # CRITICAL:
                # Do NOT accept weak candidate matches.
                # ------------------------------------------------

                if (
                    candidate_score
                    >= MIN_CANDIDATE_SCORE
                ):

                    paper = best["paper"]

                    ranking_details = best

                else:

                    print(
                        "Candidate rejected "
                        "because score is below "
                        f"{MIN_CANDIDATE_SCORE}."
                    )

        else:

            print(
                "No title candidates found."
            )

    # ========================================================
    # STEP 3 — NO PAPER FOUND
    # ========================================================

    if paper is None:

        print()
        print(
            "NO VERIFIED PAPER FOUND"
        )

        result = {

            "citation": citation,

            "exists": False,

            "matched_title": None,

            "matched_authors": [],

            "matched_year": None,

            "matched_venue": None,

            "matched_doi": None,

            "title_similarity": 0,

            "author_similarity": 0,

            "year_match": False,

            "doi_match": False,

            "venue_match": False,

            "hallucination_score": 100,

            "confidence":
                "High Risk of Hallucination",

            "reason": [
                "No sufficiently similar "
                "scholarly paper was found."
            ],

            "corrected_citation": None,
        }

        return result

    # ========================================================
    # STEP 4 — VERIFY METADATA
    # ========================================================

    verification = calculate_verification(
        parsed,
        paper,
    )

    print()
    print(
        "VERIFICATION"
    )

    print(
        "-" * 50
    )

    print(
        "Title Similarity :",
        verification[
            "title_score"
        ]
    )

    print(
        "Author Similarity:",
        verification[
            "author_score"
        ]
    )

    print(
        "Year Match       :",
        verification[
            "year_match"
        ]
    )

    print(
        "DOI Match        :",
        verification[
            "doi_match"
        ]
    )

    print(
        "Venue Match      :",
        verification[
            "venue_match"
        ]
    )

    print(
        "Hallucination Score:",
        verification[
            "hallucination_score"
        ]
    )

    # ========================================================
    # STEP 5 — EXISTENCE DECISION
    # ========================================================

    exists = determine_existence(
        verification
    )

    confidence = classify_result(
        exists,
        verification,
    )

    reasons = generate_reasons(
        verification,
        exists,
    )

    # ========================================================
    # STEP 6 — CORRECTED CITATION
    # ========================================================

    corrected = None

    if not exists:

        try:

            corrected = format_ieee(
                paper
            )

        except Exception as exc:

            print(
                "Citation formatting error:",
                exc
            )

            corrected = None

    # ========================================================
    # STEP 7 — FINAL RESULT
    # ========================================================

    print()
    print(
        "FINAL RESULT"
    )

    print(
        "-" * 50
    )

    print(
        "Paper Exists      :",
        exists
    )

    print(
        "Citation Accurate :",
        exists
    )

    print(
        "Confidence        :",
        confidence
    )

    print(
        "HallucinationScore:",
        verification[
            "hallucination_score"
        ]
    )

    print("=" * 80)

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "citation": citation,

        "exists": exists,

        "matched_title":
            paper.get(
                "title"
            ),

        "matched_authors":
            paper.get(
                "authors",
                []
            ),

        "matched_year":
            paper.get(
                "year"
            ),

        "matched_venue":
            paper.get(
                "venue"
            ),

        "matched_doi":
            paper.get(
                "doi"
            ),

        "title_similarity":
            verification[
                "title_score"
            ],

        "author_similarity":
            verification[
                "author_score"
            ],

        "year_match":
            verification[
                "year_match"
            ],

        "doi_match":
            verification[
                "doi_match"
            ],

        "venue_match":
            verification[
                "venue_match"
            ],

        "hallucination_score":
            verification[
                "hallucination_score"
            ],

        "confidence":
            confidence,

        "reason":
            reasons,

        "corrected_citation":
            corrected,
    }


# ============================================================
# VERIFY COMPLETE LLM RESPONSE
# ============================================================

def verify_response(
    llm_response: str
):

    if not llm_response:

        return []

    citations = extract_citations(
        llm_response
    )

    results = []

    print()
    print("=" * 80)
    print(
        "CITATIONS FOUND:",
        len(citations)
    )
    print("=" * 80)

    for index, citation in enumerate(
        citations,
        start=1,
    ):

        print()
        print("=" * 80)
        print(
            f"CITATION {index}"
        )
        print("=" * 80)

        print(citation)

        try:

            result = (
                verify_single_citation(
                    citation
                )
            )

            result["citation_number"] = (
                index
            )

            results.append(
                result
            )

        except Exception as exc:

            print()
            print(
                "ERROR VERIFYING CITATION:"
            )

            print(exc)

            results.append(
                {
                    "citation_number":
                        index,

                    "citation":
                        citation,

                    "exists":
                        False,

                    "matched_title":
                        None,

                    "matched_authors":
                        [],

                    "matched_year":
                        None,

                    "matched_venue":
                        None,

                    "matched_doi":
                        None,

                    "title_similarity":
                        0,

                    "author_similarity":
                        0,

                    "year_match":
                        False,

                    "doi_match":
                        False,

                    "venue_match":
                        False,

                    "hallucination_score":
                        100,

                    "confidence":
                        "Verification Error",

                    "reason": [
                        f"Verification failed: {exc}"
                    ],

                    "corrected_citation":
                        None,
                }
            )

    return results