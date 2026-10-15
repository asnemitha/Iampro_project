import re
import unicodedata
from rapidfuzz import fuzz

# ==========================================================
# Known Venue Aliases & Acronyms
# ==========================================================

VENUE_ALIASES = {
    "cvpr": [
        "computer vision and pattern recognition",
        "cvpr",
    ],
    "neurips": [
        "neural information processing systems",
        "advances in neural information processing systems",
        "nips",
        "neurips",
    ],
    "nips": [
        "neural information processing systems",
        "advances in neural information processing systems",
        "nips",
        "neurips",
    ],
    "naacl": [
        "north american chapter of the association for computational linguistics",
        "human language technologies",
        "naacl",
        "naacl hlt",
        "naacl-hlt",
    ],
    "acl": [
        "association for computational linguistics",
        "annual meeting of the association for computational linguistics",
        "acl",
    ],
    "emnlp": [
        "empirical methods in natural language processing",
        "emnlp",
    ],
    "icml": [
        "international conference on machine learning",
        "icml",
    ],
    "iclr": [
        "international conference on learning representations",
        "iclr",
    ],
    "iccv": [
        "international conference on computer vision",
        "iccv",
    ],
    "eccv": [
        "european conference on computer vision",
        "eccv",
    ],
    "aaai": [
        "association for the advancement of artificial intelligence",
        "aaai conference on artificial intelligence",
        "aaai",
    ],
    "ijcai": [
        "international joint conference on artificial intelligence",
        "ijcai",
    ],
    "arxiv": [
        "arxiv",
        "cornell university",
    ],
    "nature": [
        "nature",
    ],
    "science": [
        "science",
    ],
    "pnas": [
        "proceedings of the national academy of sciences",
        "pnas",
    ],
    "cacm": [
        "communications of the acm",
        "cacm",
    ],
}


# ==========================================================
# Generic Text Cleaning
# ==========================================================

def clean_text(text):
    if text is None:
        return ""
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("utf-8")
    return (
        text.lower()
        .replace("-", " ")
        .replace(":", " ")
        .replace(",", " ")
        .replace(".", " ")
        .replace("'", " ")
        .replace('"', " ")
        .strip()
    )


# ==========================================================
# Generic Similarity
# ==========================================================

def similarity_score(text1, text2):
    """
    Hybrid similarity score.
    Combines multiple RapidFuzz metrics for robust matching.
    """
    text1 = clean_text(text1)
    text2 = clean_text(text2)

    if not text1 or not text2:
        return 0.0

    if text1 == text2:
        return 100.0

    token = fuzz.token_sort_ratio(text1, text2)
    token_set = fuzz.token_set_ratio(text1, text2)
    partial = fuzz.partial_ratio(text1, text2)
    ratio = fuzz.ratio(text1, text2)

    score = (token * 0.4) + (token_set * 0.3) + (partial * 0.15) + (ratio * 0.15)
    return round(score, 2)


# ==========================================================
# Title Comparison
# ==========================================================

def compare_titles(original, candidate):
    if not original or not candidate:
        return {"original": original, "matched": candidate, "score": 0.0}

    c1 = clean_text(original)
    c2 = clean_text(candidate)

    if c1 == c2:
        return {"original": original, "matched": candidate, "score": 100.0}

    # If one is a direct substring of another (e.g. subtitle omitted or alternate edition)
    # Must be at least 15 characters and at least 75% of the longer title length to avoid matching generic phrases
    shorter, longer = (c1, c2) if len(c1) < len(c2) else (c2, c1)
    if len(shorter) >= 15 and len(shorter) / len(longer) >= 0.75 and shorter in longer:
        base_score = 95.0
    else:
        base_score = 0.0

    token_sort = fuzz.token_sort_ratio(c1, c2)
    token_set = fuzz.token_set_ratio(c1, c2)
    ratio = fuzz.ratio(c1, c2)

    score = max(
        base_score,
        (token_sort * 0.5) + (token_set * 0.3) + (ratio * 0.2),
        token_sort,
    )

    return {
        "original": original,
        "matched": candidate,
        "score": round(score, 2),
    }


# ==========================================================
# Author Parsing & Comparison
# ==========================================================

def parse_name(name):
    """
    Deconstruct an author name into surname and initials/given name.
    Handles 'Surname, Given', 'Given Surname', and 'G. Surname'.
    """
    raw = str(name).strip()
    norm = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("utf-8").lower()
    norm = re.sub(r"\b(dr|prof|mr|mrs|ms|phd)\b", "", norm)

    if "," in norm:
        parts = [p.strip() for p in norm.split(",") if p.strip()]
        surname = re.sub(r"[^a-z]", "", parts[0]) if parts else ""
        given = re.sub(r"[^a-z\s]", " ", parts[1]).split() if len(parts) > 1 else []
    else:
        words = re.sub(r"[^a-z\s]", " ", norm).split()
        if not words:
            return {"surname": "", "initials": [], "first": ""}
        surname = words[-1]
        given = words[:-1]

    initials = [w[0] for w in given if w]
    first = given[0] if given else ""
    return {"surname": surname, "initials": initials, "first": first}


def authors_match_single(a1, a2):
    p1 = parse_name(a1)
    p2 = parse_name(a2)

    if not p1["surname"] or not p2["surname"]:
        return False

    sur_sim = fuzz.ratio(p1["surname"], p2["surname"])
    if sur_sim < 80 and p1["surname"] not in p2["surname"] and p2["surname"] not in p1["surname"]:
        return False

    # If both have initials, the first initial must match
    if p1["initials"] and p2["initials"]:
        if p1["initials"][0] != p2["initials"][0]:
            return False

    # If both have full first names, compare them
    if len(p1["first"]) > 1 and len(p2["first"]) > 1:
        if fuzz.ratio(p1["first"], p2["first"]) < 70 and p1["first"] not in p2["first"] and p2["first"] not in p1["first"]:
            return False

    return True


def compare_authors(claimed_authors, verified_authors):
    """
    Compare author lists handling:
    - Full names vs initials (e.g. 'K. He' vs 'Kaiming He')
    - Surname-first ordering ('He, Kaiming' vs 'Kaiming He')
    - 'et al.' citations
    - Minor punctuation and accent differences
    """
    if not claimed_authors or not verified_authors:
        return 0.0

    # Clean author lists
    claimed = [
        str(a).strip()
        for a in claimed_authors
        if str(a).strip() and not str(a).strip().lower().startswith("et al")
    ]
    verified = [
        str(a).strip()
        for a in verified_authors
        if str(a).strip()
    ]

    if not claimed or not verified:
        return 100.0 if any("et al" in str(a).lower() for a in claimed_authors) else 0.0

    has_et_al = any("et al" in str(a).lower() for a in claimed_authors)

    matched_count = 0
    for c_author in claimed:
        matched = False
        for v_author in verified:
            if authors_match_single(c_author, v_author):
                matched = True
                break
        if matched:
            matched_count += 1

    # If "et al." was used and the first/available authors match
    if has_et_al and matched_count >= 1:
        match_ratio = (matched_count / len(claimed))
        if match_ratio >= 0.5:
            return 100.0

    # Normal matching ratio
    ratio = matched_count / len(claimed)
    return round(ratio * 100.0, 2)


# ==========================================================
# Year Comparison
# ==========================================================

def compare_year(claimed_year, verified_year, alternate_years=None):
    """
    Compare publication years with exact match or alternate publication years.
    """
    if claimed_year is None or verified_year is None:
        return False

    try:
        c_y = int(claimed_year)
        v_y = int(verified_year)
    except (ValueError, TypeError):
        return False

    # Exact match
    if c_y == v_y:
        return True

    # Check alternate years (e.g. reprint or preprint)
    if alternate_years:
        for alt in alternate_years:
            try:
                if c_y == int(alt):
                    return True
            except (ValueError, TypeError):
                pass

    return False


# ==========================================================
# Venue Comparison
# ==========================================================

def normalize_venue_name(v):
    if not v:
        return ""
    v = unicodedata.normalize("NFKD", str(v)).encode("ascii", "ignore").decode("utf-8").lower()
    v = re.sub(
        r"\b(proceedings of the|proceedings of|conference on|international|annual|meeting of the|journal of|transactions on|volume|vol|issue|pages|pp|the|\d{4})\b",
        " ",
        v,
    )
    v = re.sub(r"[^a-z0-9\s]", " ", v)
    return re.sub(r"\s+", " ", v).strip()


# Conferences that routinely appear as arXiv preprints in scholarly indexes
ARXIV_COMPATIBLE_CONFERENCES = {
    "neurips", "nips", "cvpr", "iclr", "icml", "acl", "emnlp", "naacl", "iccv", "eccv", "aaai", "ijcai"
}


def compare_venues(v1, v2, use_venue_fix=False, threshold=70):
    """
    Compare publication venues intelligently using acronym/alias matching,
    arXiv preprint compatibility, and normalized fuzzy overlap.
    """
    if not v1 or not v2:
        return True, 100.0

    n1 = normalize_venue_name(v1)
    n2 = normalize_venue_name(v2)

    if not n1 or not n2:
        return True, 100.0

    if n1 == n2:
        return True, 100.0

    # Check known alias groups
    for key, aliases in VENUE_ALIASES.items():
        if key in ["nature", "science"]:
            # Single-word prestigious journals must match exactly, not as substrings of other journals
            m1 = any(n1 == a or str(v1).lower().strip() == a for a in aliases)
            m2 = any(n2 == a or str(v2).lower().strip() == a for a in aliases)
        else:
            m1 = any(a in n1 for a in aliases) or any(a in str(v1).lower() for a in aliases)
            m2 = any(a in n2 for a in aliases) or any(a in str(v2).lower() for a in aliases)
        if m1 and m2:
            return True, 100.0

    # Check arXiv preprint compatibility with AI/CS conferences
    is_v1_arxiv = "arxiv" in n1 or "cornell university" in n1
    is_v2_arxiv = "arxiv" in n2 or "cornell university" in n2
    if is_v1_arxiv and not is_v2_arxiv:
        if any(conf in n2 or conf in str(v2).lower() for conf in ARXIV_COMPATIBLE_CONFERENCES):
            return True, 90.0
    elif is_v2_arxiv and not is_v1_arxiv:
        if any(conf in n1 or conf in str(v1).lower() for conf in ARXIV_COMPATIBLE_CONFERENCES):
            return True, 90.0

    # Substring containment (allowed in baseline, removed when use_venue_fix=True)
    if not use_venue_fix:
        if (len(n1) >= 3 and n1 in n2) or (len(n2) >= 3 and n2 in n1):
            return True, 95.0
        # Token set ratio handles word subsets in baseline
        score = fuzz.token_set_ratio(n1, n2)
        if score >= 70:
            return True, float(score)
        return False, float(score)
    else:
        # Venue Fix: Strict comparison (no permissive substring shortcut or loose subset overlap)
        # Evaluates token_sort_ratio requiring overall word order and token similarity
        score = fuzz.token_sort_ratio(n1, n2)
        if score >= threshold:
            return True, float(score)
        return False, float(score)


# ==========================================================
# DOI Comparison
# ==========================================================

def compare_dois(d1, d2):
    if not d1 or not d2:
        return False
    clean1 = str(d1).strip().lower().replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "").rstrip(".,;/")
    clean2 = str(d2).strip().lower().replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "").rstrip(".,;/")

    if clean1 == clean2:
        return True

    # arXiv ID equivalence (e.g. 10.48550/arxiv.1412.6980 vs arxiv:1412.6980)
    import re
    ar1 = re.search(r"(\d{4}\.\d{4,5})", clean1)
    ar2 = re.search(r"(\d{4}\.\d{4,5})", clean2)
    if ar1 and ar2 and ar1.group(1) == ar2.group(1):
        return True

    return False


# ==========================================================
# Hallucination Score
# ==========================================================

def hallucination_score(
    title_score,
    author_score,
    year_match,
    doi_match=False,
    venue_match=False,
    doi_provided=True,
    venue_provided=True,
    year_provided=True,
    citation_accurate=False,
):
    """
    Returns
    0 -> Fully genuine / verified
    100 -> Completely hallucinated
    """
    if citation_accurate:
        return 0

    score = 0

    # TITLE (50%)
    if title_score >= 95:
        score += 0
    elif title_score >= 85:
        score += 10
    elif title_score >= 70:
        score += 25
    else:
        score += 50

    # AUTHORS (20%)
    if author_score >= 85:
        score += 0
    elif author_score >= 70:
        score += 5
    elif author_score >= 50:
        score += 10
    else:
        score += 20

    # YEAR (10%) - only penalize if year was claimed and failed
    if year_provided and not year_match:
        score += 10

    # DOI (15%) - only penalize if DOI was claimed and failed
    if doi_provided and not doi_match:
        score += 15

    # VENUE (5%) - only penalize if venue was claimed and failed
    if venue_provided and not venue_match:
        score += 5

    return min(score, 100)