import requests
import re
from difflib import SequenceMatcher


# ============================================================
# CONFIGURATION
# ============================================================

CROSSREF_URL = "https://api.crossref.org/works"

TITLE_THRESHOLD = 85.0
AUTHOR_THRESHOLD = 70.0

REQUEST_TIMEOUT = 15


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update(
    {
        "User-Agent":
            "CiteGuard/1.0 "
            "(citation verification research)"
    }
)


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# STRING SIMILARITY
# ============================================================

def similarity(text1, text2):

    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    if not text1 or not text2:
        return 0.0

    return (
        SequenceMatcher(
            None,
            text1,
            text2
        ).ratio()
        * 100
    )


# ============================================================
# TITLE SIMILARITY
# ============================================================

def title_similarity(title1, title2):

    if not title1 or not title2:
        return 0.0

    score1 = similarity(
        title1,
        title2
    )

    # Token overlap helps when word order
    # is slightly different.

    words1 = set(
        normalize_text(title1).split()
    )

    words2 = set(
        normalize_text(title2).split()
    )

    if not words1 or not words2:
        return score1

    intersection = len(
        words1 & words2
    )

    union = len(
        words1 | words2
    )

    token_score = (
        intersection / union
    ) * 100

    return round(
        (score1 * 0.7)
        + (token_score * 0.3),
        2
    )


# ============================================================
# AUTHOR NORMALIZATION
# ============================================================

def normalize_author(author):

    if not author:
        return ""

    author = normalize_text(
        author
    )

    return author


# ============================================================
# AUTHOR SIMILARITY
# ============================================================

def author_similarity(
    claimed_authors,
    verified_authors
):

    if not claimed_authors:
        return 0.0

    if not verified_authors:
        return 0.0

    claimed = [
        normalize_author(a)
        for a in claimed_authors
        if normalize_author(a)
    ]

    verified = [
        normalize_author(a)
        for a in verified_authors
        if normalize_author(a)
    ]

    if not claimed or not verified:
        return 0.0

    matched = 0

    for claimed_author in claimed:

        best = 0.0

        for verified_author in verified:

            score = similarity(
                claimed_author,
                verified_author
            )

            if score > best:
                best = score

        if best >= 75:
            matched += 1

    score = (
        matched / len(claimed)
    ) * 100

    return round(
        score,
        2
    )


# ============================================================
# VENUE SIMILARITY
# ============================================================

def venue_similarity(
    venue1,
    venue2
):

    if not venue1 or not venue2:
        return 0.0

    return similarity(
        venue1,
        venue2
    )


# ============================================================
# DOI NORMALIZATION
# ============================================================

def normalize_doi(doi):

    if not doi:
        return ""

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
# YEAR EXTRACTION
# ============================================================

def extract_year(data):

    fields = [
        "published-print",
        "published-online",
        "published",
        "issued",
        "created",
    ]

    for field in fields:

        field_data = data.get(
            field
        )

        if not field_data:
            continue

        parts = field_data.get(
            "date-parts"
        )

        if not parts:
            continue

        if not parts[0]:
            continue

        try:

            return int(
                parts[0][0]
            )

        except (
            ValueError,
            TypeError
        ):
            pass

    return None


# ============================================================
# AUTHOR EXTRACTION FROM CROSSREF
# ============================================================

def extract_authors(data):

    authors = []

    for author in data.get(
        "author",
        []
    ):

        given = (
            author.get(
                "given",
                ""
            )
            or ""
        )

        family = (
            author.get(
                "family",
                ""
            )
            or ""
        )

        name = (
            f"{given} {family}"
        ).strip()

        if name:
            authors.append(
                name
            )

    return authors


# ============================================================
# VENUE EXTRACTION
# ============================================================

def extract_venue(data):

    containers = data.get(
        "container-title",
        []
    )

    if containers:

        return containers[0]

    return data.get(
        "publisher",
        ""
    )


# ============================================================
# CROSSREF METADATA CONVERSION
# ============================================================

def crossref_to_metadata(data):

    title_list = data.get(
        "title",
        []
    )

    title = ""

    if title_list:
        title = title_list[0]

    return {
        "title": title,
        "authors":
            extract_authors(data),
        "year":
            extract_year(data),
        "venue":
            extract_venue(data),
        "doi":
            normalize_doi(
                data.get(
                    "DOI",
                    ""
                )
            ),
    }


# ============================================================
# VERIFY DOI
# ============================================================

def verify_doi(
    doi: str
):

    """
    Verify DOI using Crossref.

    Returns verified scholarly
    metadata when the DOI exists.
    """

    if not doi:

        return {
            "exists": False,
            "reason":
                "No DOI provided"
        }

    doi = normalize_doi(
        doi
    )

    url = (
        f"{CROSSREF_URL}/{doi}"
    )

    try:

        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 200:

            data = (
                response.json()
                .get(
                    "message",
                    {}
                )
            )

            metadata = (
                crossref_to_metadata(
                    data
                )
            )

            metadata[
                "exists"
            ] = True

            return metadata

        return {
            "exists": False,
            "doi": doi,
            "reason":
                "DOI not found"
        }

    except Exception as e:

        return {
            "exists": False,
            "doi": doi,
            "error": str(e)
        }


# ============================================================
# SEARCH CROSSREF BY TITLE
# ============================================================

def search_by_title(
    title,
    rows=10
):

    if not title:
        return []

    params = {
        "query.title": title,
        "rows": rows,
    }

    try:

        response = session.get(
            CROSSREF_URL,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:
            return []

        data = response.json()

        items = (
            data
            .get("message", {})
            .get("items", [])
        )

        candidates = []

        for item in items:

            metadata = (
                crossref_to_metadata(
                    item
                )
            )

            if not metadata[
                "title"
            ]:
                continue

            metadata[
                "title_score"
            ] = title_similarity(
                title,
                metadata[
                    "title"
                ]
            )

            candidates.append(
                metadata
            )

        candidates.sort(
            key=lambda x:
                x.get(
                    "title_score",
                    0
                ),
            reverse=True
        )

        return candidates

    except Exception:

        return []


# ============================================================
# PARSE AUTHORS FROM CITATION
# ============================================================

def parse_authors(
    text
):

    match = re.search(
        r"Authors?\s*:\s*(.*?)(?:\n|$)",
        text,
        re.IGNORECASE
    )

    if not match:
        return []

    raw = match.group(1).strip()

    # Remove markdown formatting.

    raw = raw.replace(
        "**",
        ""
    )

    # Common author separators.

    parts = re.split(
        r";|\s+and\s+|,\s+(?=[A-Z][a-z]+(?:\s+[A-Z]\.?)?)",
        raw
    )

    authors = []

    for part in parts:

        part = part.strip()

        if part:
            authors.append(
                part
            )

    return authors


# ============================================================
# PARSE YEAR
# ============================================================

def parse_year(
    text
):

    match = re.search(
        r"(?:Year|Published(?:\s+in)?)\s*:\s*(\d{4})",
        text,
        re.IGNORECASE
    )

    if match:

        try:
            return int(
                match.group(1)
            )

        except ValueError:
            pass

    # Fallback: look for a
    # standalone publication year.

    years = re.findall(
        r"\b(19\d{2}|20\d{2})\b",
        text
    )

    if years:

        return int(
            years[0]
        )

    return None


# ============================================================
# PARSE VENUE
# ============================================================

def parse_venue(
    text
):

    match = re.search(
        r"(?:Venue|Published in)\s*:\s*(.*?)(?:\n|$)",
        text,
        re.IGNORECASE
    )

    if match:

        venue = match.group(1)

        venue = venue.replace(
            "**",
            ""
        )

        return venue.strip()

    return ""


# ============================================================
# PARSE DOI
# ============================================================

def parse_doi(
    text
):

    pattern = (
        r"(?:https?://doi\.org/)?"
        r"10\.\d{4,9}/"
        r"[-._;()/:A-Za-z0-9]+"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    doi = match.group()

    # Remove trailing punctuation
    # that commonly appears in prose.

    doi = doi.rstrip(
        ".,;:)]}"
    )

    return normalize_doi(
        doi
    )


# ============================================================
# PARSE TITLE
# ============================================================

def parse_title(
    text
):

    match = re.search(
        r"Title\s*:\s*[\"“](.*?)[\"”]",
        text,
        re.IGNORECASE
    )

    if match:

        return match.group(1).strip()

    match = re.search(
        r"Title\s*:\s*(.*?)(?:\n|$)",
        text,
        re.IGNORECASE
    )

    if match:

        title = match.group(1)

        title = title.strip()

        title = title.strip(
            "\"'“”"
        )

        return title

    return ""


# ============================================================
# PARSE CITATION
# ============================================================

def parse_citation(
    text
):

    title = parse_title(
        text
    )

    authors = parse_authors(
        text
    )

    year = parse_year(
        text
    )

    venue = parse_venue(
        text
    )

    doi = parse_doi(
        text
    )

    return {
        "raw": text,
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "doi": doi,
    }


# ============================================================
# EXTRACT CITATIONS FROM RESPONSE
# ============================================================

def extract_citations(
    text
):

    if not text:
        return []

    # If the response contains
    # explicit Title fields, split
    # around numbered citations.

    pattern = re.compile(
        r"(?=(?:^|\n)\s*(?:\d+[\.\)]|[-•])\s*)",
        re.MULTILINE
    )

    chunks = pattern.split(
        text
    )

    citations = []

    for chunk in chunks:

        if not chunk.strip():
            continue

        if re.search(
            r"Title\s*:",
            chunk,
            re.IGNORECASE
        ):

            citations.append(
                chunk.strip()
            )

    # If splitting failed,
    # treat entire input as one citation.

    if not citations:

        if re.search(
            r"Title\s*:",
            text,
            re.IGNORECASE
        ):

            citations.append(
                text.strip()
            )

    return citations


# ============================================================
# CALCULATE HALLUCINATION SCORE
# ============================================================

def calculate_hallucination_score(
    title_score,
    author_score,
    year_match,
    doi_match,
    venue_score
):

    # Correct metadata contributes
    # to a lower hallucination score.

    score = 100.0

    # Title is the strongest signal.

    score -= (
        title_score * 0.40
    )

    # Authors are important.

    score -= (
        author_score * 0.20
    )

    # Year.

    if year_match:
        score -= 10

    # DOI.

    if doi_match:
        score -= 20

    # Venue.

    score -= (
        venue_score * 0.10
    )

    # Keep score in [0, 100].

    score = max(
        0.0,
        min(
            100.0,
            score
        )
    )

    return round(
        score,
        2
    )


# ============================================================
# VERIFY ONE CITATION
# ============================================================

def verify_citation(
    citation
):

    parsed = parse_citation(
        citation
    )

    title = parsed[
        "title"
    ]

    authors = parsed[
        "authors"
    ]

    year = parsed[
        "year"
    ]

    venue = parsed[
        "venue"
    ]

    doi = parsed[
        "doi"
    ]

    print()
    print(
        "PARSED METADATA"
    )

    print(parsed)

    verified_paper = None

    # ========================================================
    # STEP 1 — DOI VERIFICATION
    # ========================================================

    if doi:

        print()
        print(
            "Searching DOI..."
        )

        doi_result = verify_doi(
            doi
        )

        if doi_result.get(
            "exists"
        ):

            verified_paper = (
                doi_result
            )

            print(
                "DOI FOUND"
            )

        else:

            print(
                "DOI NOT FOUND"
            )

    # ========================================================
    # STEP 2 — TITLE SEARCH
    # ========================================================

    candidates = []

    if title:

        print()
        print(
            "Searching by title..."
        )

        candidates = search_by_title(
            title
        )

    # ========================================================
    # CHOOSE BEST CANDIDATE
    # ========================================================

    best_candidate = None

    if candidates:

        best_candidate = (
            candidates[0]
        )

        print()
        print(
            "BEST TITLE MATCH"
        )

        print(
            "Title:",
            best_candidate[
                "title"
            ]
        )

        print(
            "Title score:",
            best_candidate[
                "title_score"
            ]
        )

    # ========================================================
    # IMPORTANT:
    # Prefer the DOI record only when
    # its title is actually compatible.
    # ========================================================

    if verified_paper:

        doi_title_score = (
            title_similarity(
                title,
                verified_paper[
                    "title"
                ]
            )
            if title
            else 100.0
        )

        if (
            doi_title_score
            >= TITLE_THRESHOLD
        ):

            selected_paper = (
                verified_paper
            )

        elif best_candidate:

            selected_paper = (
                best_candidate
            )

        else:

            selected_paper = (
                verified_paper
            )

    elif best_candidate:

        selected_paper = (
            best_candidate
        )

    else:

        selected_paper = None

    # ========================================================
    # NO PAPER FOUND
    # ========================================================

    if not selected_paper:

        return {
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

    # ========================================================
    # METADATA COMPARISON
    # ========================================================

    verified_title = (
        selected_paper.get(
            "title",
            ""
        )
    )

    verified_authors = (
        selected_paper.get(
            "authors",
            []
        )
    )

    verified_year = (
        selected_paper.get(
            "year"
        )
    )

    verified_venue = (
        selected_paper.get(
            "venue",
            ""
        )
    )

    verified_doi = normalize_doi(
        selected_paper.get(
            "doi",
            ""
        )
    )

    title_score = title_similarity(
        title,
        verified_title
    )

    author_score = author_similarity(
        authors,
        verified_authors
    )

    year_match = (
        year is not None
        and verified_year is not None
        and int(year)
        == int(verified_year)
    )

    doi_match = (
        bool(doi)
        and bool(verified_doi)
        and normalize_doi(doi)
        == verified_doi
    )

    venue_score = venue_similarity(
        venue,
        verified_venue
    )

    venue_match = (
        venue_score >= 80
    )

    # ========================================================
    # DECISION LOGIC
    # ========================================================

    # A citation is considered valid only when
    # the requested paper's metadata is sufficiently
    # consistent with the scholarly record.
    #
    # DOI match alone is NOT enough.
    #
    # This is important for detecting:
    # - fake authors
    # - wrong year
    # - fake venue
    # - wrong DOI
    # - fabricated metadata

    title_ok = (
        title_score
        >= TITLE_THRESHOLD
    )

    authors_ok = (
        not authors
        or author_score
        >= AUTHOR_THRESHOLD
    )

    # If a DOI was explicitly supplied,
    # it must match.
    doi_ok = (
        not doi
        or doi_match
    )

    year_ok = (
        year is None
        or year_match
    )

    venue_ok = (
        not venue
        or venue_match
    )

    exists = (
        title_ok
        and authors_ok
        and doi_ok
        and year_ok
        and venue_ok
    )

    # ========================================================
    # HALLUCINATION SCORE
    # ========================================================

    hallucination = (
        calculate_hallucination_score(
            title_score,
            author_score,
            year_match,
            doi_match,
            venue_score
        )
    )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    if exists:

        confidence = (
            "Verified Citation"
        )

    elif title_score >= 80:

        confidence = (
            "Paper Exists but "
            "Citation Contains Errors"
        )

    elif title_score >= 60:

        confidence = (
            "Possible Match"
        )

    else:

        confidence = (
            "High Risk of Hallucination"
        )

    # ========================================================
    # REASONS
    # ========================================================

    reasons = []

    if title_score < TITLE_THRESHOLD:

        reasons.append(
            "Paper title differs."
        )

    if authors and (
        author_score
        < AUTHOR_THRESHOLD
    ):

        reasons.append(
            "Authors differ."
        )

    if year is not None and not year_match:

        reasons.append(
            "Publication year differs."
        )

    if doi and not doi_match:

        reasons.append(
            "DOI differs."
        )

    if venue and not venue_match:

        reasons.append(
            "Publication venue differs."
        )

    if not reasons:

        reasons.append(
            "Citation metadata matches "
            "the verified scholarly record."
        )

    # ========================================================
    # CORRECTED CITATION
    # ========================================================

    corrected = (
        f'{verified_title}. '
        f'{", ".join(verified_authors)}. '
        f'{verified_venue}, '
        f'{verified_year}. '
        f'DOI: {verified_doi}'
    )

    # ========================================================
    # PRINT VERIFICATION
    # ========================================================

    print()
    print(
        "VERIFICATION"
    )

    print(
        "-" * 60
    )

    print(
        "Title Similarity :",
        round(
            title_score,
            2
        )
    )

    print(
        "Author Similarity:",
        round(
            author_score,
            2
        )
    )

    print(
        "Year Match       :",
        year_match
    )

    print(
        "DOI Match        :",
        doi_match
    )

    print(
        "Venue Match      :",
        venue_match
    )

    print(
        "Hallucination    :",
        hallucination
    )

    print()
    print(
        "FINAL RESULT"
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

    return {
        "citation": citation,

        "exists": exists,

        "matched_title":
            verified_title,

        "matched_authors":
            verified_authors,

        "matched_year":
            verified_year,

        "matched_venue":
            verified_venue,

        "matched_doi":
            verified_doi,

        "title_similarity":
            round(
                title_score,
                2
            ),

        "author_similarity":
            round(
                author_score,
                2
            ),

        "year_match":
            year_match,

        "doi_match":
            doi_match,

        "venue_match":
            venue_match,

        "hallucination_score":
            hallucination,

        "confidence":
            confidence,

        "reason":
            reasons,

        "corrected_citation":
            corrected
            if not exists
            else None,
    }


# ============================================================
# VERIFY COMPLETE RESPONSE
# ============================================================

def verify_response(
    llm_response: str
):

    """
    Main function used by the CiteGuard
    evaluation pipeline and API.

    Takes an LLM response containing
    one or more citations and returns
    a list of verification results.
    """

    if not llm_response:

        return []

    citations = extract_citations(
        llm_response
    )

    results = []

    print()
    print(
        "=" * 80
    )

    print(
        "CITATIONS FOUND:",
        len(citations)
    )

    print(
        "=" * 80
    )

    for index, citation in enumerate(
        citations,
        start=1
    ):

        print()
        print(
            "=" * 80
        )

        print(
            f"CITATION {index}"
        )

        print(
            "=" * 80
        )

        try:

            result = verify_citation(
                citation
            )

            result[
                "citation_number"
            ] = index

            results.append(
                result
            )

        except Exception as exc:

            print()
            print(
                "Verification error:",
                exc
            )

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
                        str(exc)
                    ],

                    "corrected_citation":
                        None,
                }
            )

    return results


# ============================================================
# BACKWARD-COMPATIBLE TEXT VERIFICATION
# ============================================================

def verify_text(
    text: str
):

    """
    Existing compatibility function.

    If a DOI exists, verify the DOI.
    Otherwise perform complete citation
    verification.
    """

    if not text:

        return {
            "exists": False,
            "reason":
                "Empty text"
        }

    doi_pattern = (
        r"10\.\d{4,9}/"
        r"[-._;()/:A-Za-z0-9]+"
    )

    match = re.search(
        doi_pattern,
        text
    )

    if match:

        doi = match.group().rstrip(
            ".,;:)]}"
        )

        return verify_doi(
            doi
        )

    # No DOI — use complete
    # metadata verification.

    result = verify_citation(
        text
    )

    return result