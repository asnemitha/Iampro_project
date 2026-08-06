from rapidfuzz import fuzz


# ==========================================================
# Generic Text Cleaning
# ==========================================================

def clean_text(text):

    if text is None:
        return ""

    return (
        text.lower()
        .replace("-", " ")
        .replace(":", " ")
        .replace(",", " ")
        .replace(".", " ")
        .strip()
    )


# ==========================================================
# Generic Similarity
# ==========================================================

def similarity_score(text1, text2):
    """
    Hybrid similarity score.

    Combines multiple RapidFuzz metrics
    for much better matching.
    """

    text1 = clean_text(text1)
    text2 = clean_text(text2)

    if not text1 or not text2:
        return 0

    token = fuzz.token_sort_ratio(text1, text2)

    partial = fuzz.partial_ratio(text1, text2)

    ratio = fuzz.ratio(text1, text2)

    return round(
        (token * 0.5)
        + (partial * 0.3)
        + (ratio * 0.2),
        2,
    )


# ==========================================================
# Title Comparison
# ==========================================================

def compare_titles(original, crossref):

    score = similarity_score(
        original,
        crossref,
    )

    return {

        "original": original,

        "matched": crossref,

        "score": score,

    }


# ==========================================================
# Author Comparison
# ==========================================================

def compare_authors(original, crossref):

    if not original or not crossref:
        return 0

    original = " ".join(original)

    crossref = " ".join(crossref)

    return similarity_score(
        original,
        crossref,
    )


# ==========================================================
# Year Comparison
# ==========================================================

def compare_year(original, crossref):

    if original is None:
        return False

    if crossref is None:
        return False

    return int(original) == int(crossref)


# ==========================================================
# Hallucination Score
# ==========================================================

def hallucination_score(
    title_score,
    author_score,
    year_match,
    doi_match=False,
    venue_match=False,
):
    """
    Returns

    0 -> Fully genuine

    100 -> Completely hallucinated
    """

    score = 0

    # -------------------------
    # TITLE (50%)
    # -------------------------

    if title_score >= 98:
        score += 0

    elif title_score >= 95:
        score += 5

    elif title_score >= 90:
        score += 10

    elif title_score >= 80:
        score += 20

    elif title_score >= 70:
        score += 35

    else:
        score += 50

    # -------------------------
    # AUTHORS (20%)
    # -------------------------

    if author_score >= 95:
        score += 0

    elif author_score >= 85:
        score += 5

    elif author_score >= 70:
        score += 10

    elif author_score >= 50:
        score += 15

    else:
        score += 20

    # -------------------------
    # YEAR (10%)
    # -------------------------

    if not year_match:
        score += 10

    # -------------------------
    # DOI (15%)
    # -------------------------

    if not doi_match:
        score += 15

    # -------------------------
    # VENUE (5%)
    # -------------------------

    if not venue_match:
        score += 5

    return min(score, 100)