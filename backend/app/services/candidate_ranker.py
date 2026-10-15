from app.services.similarity_service import (
    compare_titles,
    compare_authors,
    compare_year,
    compare_venues,
    compare_dois,
)

from app.services.metadata_normalizer import (
    normalize_metadata,
)

# ==========================================================
# Weights
# ==========================================================

TITLE_WEIGHT = 0.40
AUTHOR_WEIGHT = 0.25
YEAR_WEIGHT = 0.15
VENUE_WEIGHT = 0.10
DOI_WEIGHT = 0.05
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

def venue_similarity(v1, v2, use_venue_fix=False, threshold=70):
    is_match, score = compare_venues(v1, v2, use_venue_fix=use_venue_fix, threshold=threshold)
    return score if is_match else score * 0.5


# ==========================================================
# DOI Similarity
# ==========================================================

def doi_similarity(d1, d2):
    return 100 if compare_dois(d1, d2) else 0


# ==========================================================
# Candidate Ranking
# ==========================================================

def rank_candidates(parsed_metadata, candidates, use_venue_fix=False, prefers_original=False, venue_threshold=70):

    if not candidates:
        return []

    # If prefers_original, find the earliest publication year among matching candidates
    min_year = None
    if prefers_original:
        valid_years = []
        for c in candidates:
            if not c or not c.get("year"):
                continue
            t_sim = compare_titles(parsed_metadata.get("title"), c.get("title"))["score"]
            a_sim = compare_authors(parsed_metadata.get("authors"), c.get("authors"))
            if t_sim >= 80 and a_sim >= 60:
                valid_years.append(c["year"])
        if valid_years:
            min_year = min(valid_years)

    ranked = []

    for candidate in candidates:
        if not candidate:
            continue

        title_res = compare_titles(
            parsed_metadata.get("title"),
            candidate.get("title")
        )
        title_score = title_res["score"]

        author_score = compare_authors(
            parsed_metadata.get("authors"),
            candidate.get("authors")
        )

        year_match = compare_year(
            parsed_metadata.get("year"),
            candidate.get("year"),
            candidate.get("alternate_years")
        )
        year_score = 100 if year_match else 0

        venue_match, venue_sim = compare_venues(
            parsed_metadata.get("venue"),
            candidate.get("venue"),
            use_venue_fix=use_venue_fix,
            threshold=venue_threshold,
        )
        venue_score = venue_sim if venue_match else venue_sim * 0.5

        doi_match = compare_dois(
            parsed_metadata.get("doi"),
            candidate.get("doi")
        )
        doi_score = 100 if doi_match else 0

        source_name = candidate.get("source") or "Crossref"
        source_score = SOURCE_SCORE.get(source_name, 80)

        # Base weighted score
        final_score = (
            TITLE_WEIGHT * title_score +
            AUTHOR_WEIGHT * author_score +
            YEAR_WEIGHT * year_score +
            VENUE_WEIGHT * venue_score +
            DOI_WEIGHT * doi_score +
            SOURCE_WEIGHT * source_score
        )

        # Authoritative DOI boost: If DOI matches and title matches, or authors match with year/venue/title corroboration
        if doi_match and (title_score >= 70 or author_score >= 60 or (year_score == 100 and venue_score >= 80)):
            final_score += 25.0

        # Penalty for authorless candidate when citation explicitly provided authors
        parsed_has_authors = bool(parsed_metadata.get("authors") and len(parsed_metadata["authors"]) > 0)
        cand_has_authors = bool(candidate.get("authors") and len(candidate.get("authors", [])) > 0)
        if parsed_has_authors and not cand_has_authors:
            final_score -= 25.0

        # Penalty for book chapter / collection distractor when not the cited DOI
        cand_doi_str = str(candidate.get("doi") or "").lower()
        is_book_record = (
            "/978" in cand_doi_str
            or "/b978" in cand_doi_str
            or "crc press" in str(candidate.get("publisher") or "").lower()
            or "encyclopedia" in (candidate.get("venue") or "").lower()
        )
        if is_book_record and not doi_match:
            final_score -= 20.0

        # High-confidence identity bonus: title >= 90 and author >= 80
        if title_score >= 90 and author_score >= 80:
            final_score += 10.0

        # Original publication preference bonus / penalty
        if prefers_original and min_year is not None:
            cand_year = candidate.get("year")
            if cand_year:
                if cand_year <= min_year + 1:
                    final_score += 15.0
                elif cand_year > min_year + 1:
                    final_score -= 15.0

            c_venue = (candidate.get("venue") or "").lower()
            c_title = (candidate.get("title") or "").lower()
            if cand_year and cand_year > min_year:
                if any(w in c_venue or w in c_title for w in ["communications of the acm", "survey", "review", "overview", "reprint", "retrospective"]):
                    final_score -= 15.0

        ranked.append({
            "paper": candidate,
            "title_score": round(title_score, 2),
            "author_score": round(author_score, 2),
            "year_score": year_score,
            "venue_score": round(venue_score, 2),
            "doi_score": doi_score,
            "source_score": source_score,
            "final_score": round(min(max(final_score, 0.0), 100.0), 2),
        })

    ranked.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return ranked