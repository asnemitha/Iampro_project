import re
from app.services.similarity_service import (
    compare_titles,
    compare_authors,
    compare_year,
    compare_venues,
    compare_dois,
)


def extract_prompt_metadata(prompt: str) -> dict:
    """
    Extract citation metadata requested in a user prompt.

    Extracts:
    - title
    - authors
    - year
    - venue
    - doi
    - arxiv
    """
    if not prompt:
        return {
            "title": None,
            "authors": [],
            "year": None,
            "venue": None,
            "doi": None,
            "arxiv": None,
            "prefers_original": False,
        }

    result = {
        "title": None,
        "authors": [],
        "year": None,
        "venue": None,
        "doi": None,
        "arxiv": None,
        "prefers_original": bool(
            re.search(r"\boriginal\s+(?:paper|publication|work|version|article)\b", prompt, re.IGNORECASE)
        ),
    }

    # 1. DOI
    doi_match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", prompt, re.IGNORECASE)
    if doi_match:
        result["doi"] = doi_match.group().rstrip(".,;:)]}")

    # 2. arXiv
    arxiv_match = re.search(r"\barXiv:\s*(\d{4}\.\d{4,5})\b", prompt, re.IGNORECASE)
    if arxiv_match:
        result["arxiv"] = f"arXiv:{arxiv_match.group(1)}"

    # 3. Explicit Title or Quoted Title
    title_match = re.search(r"Title\s*:\s*([^\n,]+)", prompt, re.IGNORECASE)
    if title_match:
        raw_t = title_match.group(1).strip().strip("\"'“”")
        raw_t = re.split(r"\s+(?:Authors?|Venue|Conference|Year|DOI|arXiv):", raw_t, flags=re.IGNORECASE)[0]
        result["title"] = raw_t.strip("\"'“” ")
    else:
        # Check quoted string following cite / paper / titled / work
        quoted_match = re.search(r"(?:cite|paper|titled|article|work)\s+(?:the\s+)?(?:original\s+)?(?:paper\s+)?['\"“]([^'\"”\n]{5,})['\"”]", prompt, re.IGNORECASE)
        if quoted_match:
            result["title"] = quoted_match.group(1).strip()
        else:
            # Any quoted string of sufficient length (>= 6 chars)
            quoted_any = re.search(r"['\"“]([^'\"”\n]{6,})['\"”]", prompt)
            if quoted_any:
                result["title"] = quoted_any.group(1).strip()

    # 4. Authors
    author_line = re.search(r"Authors?\s*:\s*([^\n]+)", prompt, re.IGNORECASE)
    if author_line:
        author_raw = author_line.group(1).strip()
    else:
        by_match = re.search(
            r"\bby\s+([A-Z][a-zA-Z\s,]+?)(?:,\s*(?:published|in\s+(?:19|20)\d{2}|with\s+DOI|DOI:)|published|\.|\$|\n|Year:|Venue:|DOI:|arXiv:)",
            prompt
        )
        if by_match:
            author_raw = by_match.group(1).strip()
        else:
            author_raw = ""

    if author_raw:
        # Clean out non-author fragments
        author_raw = re.split(
            r"\n|Year:|Venue:|Conference:|Journal:|Booktitle:|DOI:|arXiv:|published\s+in|published|in\s+(?:19|20)\d{2}",
            author_raw,
            flags=re.IGNORECASE
        )[0]
        author_raw = author_raw.replace("et al.", "").replace("et al", "")
        authors = re.split(r",|;| and ", author_raw)
        result["authors"] = [
            a.strip(" .\"'")
            for a in authors
            if a.strip(" .\"'") and not re.match(r"^(?:published|in|\d{4})$", a.strip(" .\"'"), re.IGNORECASE)
        ]

    # 5. Year
    year_line = re.search(r"Year\s*:\s*((?:19|20)\d{2})\b", prompt, re.IGNORECASE)
    if year_line:
        result["year"] = int(year_line.group(1))
    else:
        # Check "published in 2019" or "in 2019"
        pub_year = re.search(r"(?:published\s+in|in|of)\s+((?:19|20)\d{2})\b", prompt, re.IGNORECASE)
        if pub_year:
            result["year"] = int(pub_year.group(1))
        else:
            # Check standalone year (avoid picking years from DOIs)
            clean_prompt_no_doi = re.sub(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", "", prompt)
            all_years = re.findall(r"\b(?:19|20)\d{2}\b", clean_prompt_no_doi)
            if all_years:
                result["year"] = int(all_years[-1])

    # 6. Venue
    venue_line = re.search(r"(?:Venue|Conference|Journal|Booktitle)\s*:\s*([^\n]+)", prompt, re.IGNORECASE)
    if venue_line:
        result["venue"] = venue_line.group(1).strip().rstrip(".,;")
    else:
        # Check "published in <Venue>"
        pub_venue = re.search(
            r"published\s+in\s+([A-Za-z0-9\s-]+?)(?:,\s*(?:19|20)\d{2}|\s+(?:19|20)\d{2}|\n|DOI:|\.|\$)",
            prompt,
            re.IGNORECASE
        )
        if pub_venue:
            v = pub_venue.group(1).strip()
            if not re.match(r"^(?:19|20)\d{2}$", v):
                result["venue"] = v

    return result


def check_prompt_consistency(user_prompt: str, generated_citation: dict, matched_paper: dict = None) -> dict:
    """
    Compare citation metadata requested by user in prompt against generated citation.

    Distinguishes:
    A) Bibliographic validity of generated citation (evaluated separately)
    B) Prompt consistency: whether generated citation matched what was requested

    Returns structured prompt consistency object.
    """
    if not user_prompt:
        return None

    requested = extract_prompt_metadata(user_prompt)

    has_requested = bool(
        requested.get("title")
        or requested.get("authors")
        or requested.get("year")
        or requested.get("venue")
        or requested.get("doi")
    )

    if not has_requested:
        return {
            "checked": False,
            "matches": True,
            "mismatched_fields": [],
            "requested_metadata": requested,
            "generated_metadata": {
                "title": generated_citation.get("title"),
                "authors": generated_citation.get("authors", []),
                "year": generated_citation.get("year"),
                "venue": generated_citation.get("venue"),
                "doi": generated_citation.get("doi"),
            },
            "requested_authors": requested.get("authors", []),
            "generated_authors": generated_citation.get("authors", []),
            "explanation": "No specific citation metadata was requested in the prompt.",
        }

    mismatched_fields = []
    comparisons = {}

    # 1. Title comparison
    if requested.get("title") and generated_citation.get("title"):
        t_sim = compare_titles(requested["title"], generated_citation["title"])
        comparisons["title_similarity"] = t_sim["score"]
        if t_sim["score"] < 75:
            mismatched_fields.append("title")

    # 2. Authors comparison
    if requested.get("authors") and generated_citation.get("authors"):
        a_sim = compare_authors(requested["authors"], generated_citation["authors"])
        comparisons["author_similarity"] = a_sim
        if a_sim < 70:
            mismatched_fields.append("authors")

    # 3. Year comparison
    if requested.get("year") and generated_citation.get("year"):
        alts = matched_paper.get("alternate_years") if matched_paper else None
        y_match = compare_year(requested["year"], generated_citation["year"], alts)
        comparisons["year_match"] = y_match
        if not y_match:
            mismatched_fields.append("year")

    # 4. Venue comparison
    if requested.get("venue") and generated_citation.get("venue"):
        v_match, _ = compare_venues(requested["venue"], generated_citation["venue"])
        comparisons["venue_match"] = v_match
        if not v_match:
            mismatched_fields.append("venue")

    # 5. DOI comparison
    if requested.get("doi") and generated_citation.get("doi"):
        d_match = compare_dois(requested["doi"], generated_citation["doi"])
        comparisons["doi_match"] = d_match
        if not d_match:
            mismatched_fields.append("doi")

    matches = (len(mismatched_fields) == 0)

    # Build human-readable explanation
    if matches:
        explanation = "The generated citation matches the metadata requested in the prompt."
    else:
        reasons = []
        if "authors" in mismatched_fields:
            req_a = ", ".join(requested.get("authors", []))
            gen_a = ", ".join(generated_citation.get("authors", []))
            if matched_paper and matched_paper.get("authors"):
                true_authors = matched_paper["authors"]
                true_a = ", ".join(true_authors[:3]) + (" et al." if len(true_authors) > 3 else "")
                reasons.append(f"The LLM cited the true authors of the paper ({true_a}), but deviated from the authors requested in the user prompt ({req_a}).")
            else:
                reasons.append(f"The LLM cited authors ({gen_a}), but deviated from the authors requested in the user prompt ({req_a}).")
        if "year" in mismatched_fields:
            reasons.append(f"The LLM cited publication year {generated_citation.get('year')} rather than the year {requested.get('year')} requested in the prompt.")
        if "title" in mismatched_fields:
            reasons.append(f"The LLM cited '{generated_citation.get('title')}' rather than the title '{requested.get('title')}' requested in the prompt.")
        if "venue" in mismatched_fields:
            reasons.append(f"The LLM cited venue '{generated_citation.get('venue')}' rather than the venue '{requested.get('venue')}' requested in the prompt.")
        if "doi" in mismatched_fields:
            reasons.append(f"The LLM cited DOI '{generated_citation.get('doi')}' rather than the DOI '{requested.get('doi')}' requested in the prompt.")
        explanation = " ".join(reasons)

    return {
        "checked": True,
        "matches": matches,
        "mismatched_fields": mismatched_fields,
        "requested_metadata": requested,
        "generated_metadata": {
            "title": generated_citation.get("title"),
            "authors": generated_citation.get("authors", []),
            "year": generated_citation.get("year"),
            "venue": generated_citation.get("venue"),
            "doi": generated_citation.get("doi"),
        },
        "requested_authors": requested.get("authors", []),
        "generated_authors": generated_citation.get("authors", []),
        "comparisons": comparisons,
        "explanation": explanation,
    }
