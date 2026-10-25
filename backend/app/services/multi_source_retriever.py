from app.services import (
    crossref_service,
    semantic_scholar_service,
    openalex_service,
    datacite_service,
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
    Retrieve candidate papers from multiple scholarly databases:
    Crossref, Semantic Scholar, OpenAlex, and DataCite.

    Returns one merged candidate list with source provenance.
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
    crossref = crossref_service.verify_title(title, rows=10)
    if author_term:
        cr_with_author = crossref_service.verify_title(title, author=author_term, rows=5)
        crossref.extend(cr_with_author)

    # Step 2: Query Semantic Scholar
    semantic = semantic_scholar_service.search_semantic_scholar(title)

    # Step 3: Query OpenAlex by title
    openalex = openalex_service.search_openalex(title, limit=10)
    if author_term:
        oa_with_author = openalex_service.search_openalex(title, author=author_term, limit=10)
        openalex.extend(oa_with_author)

    # Step 4: Query DataCite by title and author
    datacite = datacite_service.search_datacite(title, author=author_term, limit=10)

    # Evaluate provider retrieval status
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

    if datacite_service.last_status.get("success", True):
        p_success += 1
    else:
        p_failed += 1
        errors["datacite"] = datacite_service.last_status.get("error")

    last_retrieval_status["providers_queried"] = 4
    last_retrieval_status["providers_successful"] = p_success
    last_retrieval_status["providers_failed"] = p_failed
    last_retrieval_status["errors"] = errors
    last_retrieval_status["all_failed"] = (p_success == 0 and p_failed > 0)

    merged = []

    for paper in crossref + semantic + openalex + datacite:
        if not paper or not paper.get("title"):
            continue

        if not paper.get("provenance"):
            paper["provenance"] = {
                "primary_source": paper.get("source", "Crossref"),
                "retrieved_title": paper.get("title"),
                "retrieved_authors": list(paper.get("authors") or []),
                "retrieved_year": paper.get("year"),
                "retrieved_venue": paper.get("venue"),
                "retrieved_doi": paper.get("doi"),
                "sources_corroborating": [paper.get("source", "Crossref")],
            }

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
                    # If both have publication years and they differ by more than 2 years,
                    # keep them as distinct candidate versions (e.g. 2014 original vs 2020 reprint/survey)
                    if c_y and p_y and abs(c_y - p_y) > 2:
                        continue
                    existing = cand
                    break

        if existing is not None:
            # Track corroborating source provenance
            if not existing.get("provenance"):
                existing["provenance"] = {
                    "primary_source": existing.get("source", "Crossref"),
                    "retrieved_title": existing.get("title"),
                    "retrieved_authors": list(existing.get("authors") or []),
                    "retrieved_year": existing.get("year"),
                    "retrieved_venue": existing.get("venue"),
                    "retrieved_doi": existing.get("doi"),
                    "sources_corroborating": [existing.get("source", "Crossref")],
                }
            src = paper.get("source")
            if src and src not in existing["provenance"]["sources_corroborating"]:
                existing["provenance"]["sources_corroborating"].append(src)

            # Merge alternate_years
            all_alts = set(existing.get("alternate_years", []) or [])
            all_alts.update(paper.get("alternate_years", []) or [])
            if existing.get("year"):
                all_alts.add(existing["year"])
            if paper.get("year"):
                all_alts.add(paper["year"])
            existing["alternate_years"] = sorted(list(all_alts))

            # Prefer the earliest primary publication year
            if paper.get("year"):
                if not existing.get("year"):
                    existing["year"] = paper["year"]
                elif paper["year"] < existing["year"]:
                    existing["year"] = paper["year"]

            # If existing has no venue or generic venue but new record has venue, use it
            if not existing.get("venue") and paper.get("venue"):
                existing["venue"] = paper["venue"]
            elif existing.get("venue") == "arXiv" and paper.get("venue") and paper.get("venue") != "arXiv":
                # If existing is arXiv but new record has conference/journal venue, keep conference venue
                existing["venue"] = paper["venue"]

            # If existing has fewer authors, update
            if len(p_authors) > len(existing.get("authors", [])):
                existing["authors"] = p_authors

            # If existing has no DOI or has a predatory mirror DOI (10.65215), adopt canonical DOI
            if paper.get("doi"):
                e_doi = str(existing.get("doi") or "")
                p_doi = str(paper.get("doi") or "")
                if not e_doi or e_doi.startswith("10.65215"):
                    existing["doi"] = p_doi
                elif p_doi.startswith("10.48550/arxiv") and not (e_doi.startswith("10.11") or e_doi.startswith("10.10")):
                    existing["doi"] = p_doi

            # If existing has no abstract but new has abstract, copy it
            if not existing.get("abstract") and paper.get("abstract"):
                existing["abstract"] = paper["abstract"]

            continue

        merged.append(paper)

    return merged
