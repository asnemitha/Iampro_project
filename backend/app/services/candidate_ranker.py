from app.services.similarity_service import (
    compare_titles,
    compare_authors,
    compare_year,
)

from app.services.metadata_normalizer import (
    normalize_metadata,
)

# ==========================================================
# Weights
# ==========================================================

TITLE_WEIGHT = 0.40
AUTHOR_WEIGHT = 0.20
YEAR_WEIGHT = 0.10
VENUE_WEIGHT = 0.10
DOI_WEIGHT = 0.15
SOURCE_WEIGHT = 0.05


# ==========================================================
# Source Reliability
# ==========================================================

SOURCE_SCORE = {

    "Crossref": 100,

    "Semantic Scholar": 95,

    "OpenAlex": 90,

}


# ==========================================================
# Venue Similarity
# ==========================================================

def venue_similarity(v1, v2):

    if not v1 or not v2:
        return 0

    v1 = v1.lower().strip()
    v2 = v2.lower().strip()

    if v1 == v2:
        return 100

    if v1 in v2 or v2 in v1:
        return 90

    words1 = set(v1.split())
    words2 = set(v2.split())

    if not words1 or not words2:
        return 0

    return (
        len(words1 & words2)
        /
        len(words1 | words2)
    ) * 100


# ==========================================================
# DOI Similarity
# ==========================================================

def doi_similarity(d1, d2):

    if not d1 or not d2:
        return 0

    if d1.lower().strip() == d2.lower().strip():
        return 100

    return 0


# ==========================================================
# Candidate Ranking
# ==========================================================

def rank_candidates(parsed_metadata, candidates):

    if not candidates:
        return []

    parsed = normalize_metadata(parsed_metadata)

    ranked = []

    for candidate in candidates:

        normalized = normalize_metadata(candidate)

        title_score = compare_titles(

            parsed["title"],
            normalized["title"]

        )["score"]

        author_score = compare_authors(

            parsed["authors"],
            normalized["authors"]

        )

        year_score = (

            100

            if compare_year(
                parsed["year"],
                normalized["year"]
            )

            else 0

        )

        venue_score = venue_similarity(

            parsed["venue"],
            normalized["venue"]

        )

        doi_score = doi_similarity(

            parsed.get("doi"),
            normalized.get("doi")

        )

        source_score = SOURCE_SCORE.get(

            candidate.get("source"),

            80

        )

        final_score = (

            TITLE_WEIGHT * title_score +

            AUTHOR_WEIGHT * author_score +

            YEAR_WEIGHT * year_score +

            VENUE_WEIGHT * venue_score +

            DOI_WEIGHT * doi_score +

            SOURCE_WEIGHT * source_score

        )

        ranked.append({

            "paper": candidate,

            "title_score": round(title_score, 2),

            "author_score": round(author_score, 2),

            "year_score": year_score,

            "venue_score": round(venue_score, 2),

            "doi_score": doi_score,

            "source_score": source_score,

            "final_score": round(final_score, 2),

        })

    ranked.sort(

        key=lambda x: x["final_score"],

        reverse=True

    )

    return ranked