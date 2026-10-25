from app.services.crossref_service import verify_title
from app.services.semantic_scholar_service import (
    search_semantic_scholar,
)
from app.services.openalex_service import (
    search_openalex,
)


# Provider retrieval telemetry
last_retrieval_status = {
    "providers_queried": 0,
    "providers_successful": 0,
    "providers_failed": 0,
    "errors": {},
    "all_failed": False,
}


def retrieve_candidates(title, authors=None, year=None, doi=None):
    """
    Retrieve candidate papers from multiple scholarly databases.

    Returns one merged candidate list.
    """

    if not title:
        last_retrieval_status["all_failed"] = False
        return []

    first_author = authors[0] if (authors and len(authors) > 0) else None
    author_term = None
    if first_author:
        from app.services.similarity_service import parse_name
        author_term = parse_name(first_author).get("surname") or first_author

    # Step 1: Query Crossref by title
    crossref = verify_title(title, rows=10)
    if author_term:
        cr_with_author = verify_title(title, author=author_term, rows=5)
        crossref.extend(cr_with_author)

    # Step 2: Query Semantic Scholar
    semantic = search_semantic_scholar(title)

    # Step 3: Query OpenAlex by title
    openalex = search_openalex(title, limit=10)
    if author_term:
        oa_with_author = search_openalex(title, author=author_term, limit=10)
        openalex.extend(oa_with_author)

    # Evaluate provider retrieval status
    from app.services import crossref_service, semantic_scholar_service, openalex_service

    p_success = 0
    p_failed = 0
    errors = {}

    if crossref_service.last_status.get("success", True):
        p_success += 1
    else:
        p_failed += 1
        errors["crossref"] = crossref_service.last_status.get("error")

    if semantic_scholar_service.last_status.get("success", True):
        p_success += 1
    else:
        p_failed += 1
        errors["semantic_scholar"] = semantic_scholar_service.last_status.get("error")

    if openalex_service.last_status.get("success", True):
        p_success += 1
    else:
        p_failed += 1
        errors["openalex"] = openalex_service.last_status.get("error")

    last_retrieval_status["providers_queried"] = 3
    last_retrieval_status["providers_successful"] = p_success
    last_retrieval_status["providers_failed"] = p_failed
    last_retrieval_status["errors"] = errors
    last_retrieval_status["all_failed"] = (p_success == 0 and p_failed > 0)

    merged = []

    for paper in crossref + semantic + openalex:
        if not paper or not paper.get("title"):
            continue

        p_title = paper.get("title", "").strip().lower()
        p_authors = paper.get("authors", [])

        # Find existing candidate with same title AND matching authors
        existing = None
        for cand in merged:
            c_t = cand.get("title", "").strip().lower()
            same_title = (c_t == p_title)
            if not same_title:
                from app.services.similarity_service import compare_titles
                same_title = (compare_titles(c_t, p_title)["score"] >= 88)
            if same_title:
                # If authors match or either has no authors, they are the same paper
                from app.services.similarity_service import compare_authors
                if not cand.get("authors") or not p_authors or compare_authors(cand.get("authors"), p_authors) >= 60:
                    c_y = cand.get("year")
                    p_y = paper.get("year")
                    # If both have publication years and they differ by more than 1 year,
                    # keep them as distinct candidate versions (e.g. 2014 original vs 2020 reprint/survey)
                    if c_y and p_y and abs(c_y - p_y) > 1:
                        continue
                    existing = cand
                    break

        if existing is not None:
            # Merge alternate_years
            all_alts = set(existing.get("alternate_years", []) or [])
            all_alts.update(paper.get("alternate_years", []) or [])
            if existing.get("year"):
                all_alts.add(existing["year"])
            if paper.get("year"):
                all_alts.add(paper["year"])
            existing["alternate_years"] = sorted(list(all_alts))

            # Update year according to source reliability priority (Crossref > Semantic Scholar > OpenAlex)
            SOURCE_PRIO = {"Crossref": 3, "Semantic Scholar": 2, "OpenAlex": 1}
            e_prio = SOURCE_PRIO.get(existing.get("source"), 0)
            p_prio = SOURCE_PRIO.get(paper.get("source"), 0)

            if paper.get("year"):
                if not existing.get("year"):
                    existing["year"] = paper["year"]
                elif p_prio > e_prio:
                    existing["year"] = paper["year"]
                elif p_prio == e_prio and paper["year"] < existing["year"]:
                    existing["year"] = paper["year"]

            # If existing has no venue but new record has venue, use it
            if not existing.get("venue") and paper.get("venue"):
                existing["venue"] = paper["venue"]

            # If existing has fewer authors, update
            if len(p_authors) > len(existing.get("authors", [])):
                existing["authors"] = p_authors

            # If existing has no DOI but new has DOI, copy it
            if not existing.get("doi") and paper.get("doi"):
                existing["doi"] = paper["doi"]

            # If existing has no abstract but new has abstract, copy it
            if not existing.get("abstract") and paper.get("abstract"):
                existing["abstract"] = paper["abstract"]

            continue

        merged.append(paper)

    return merged
