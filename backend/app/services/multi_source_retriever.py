from app.services.crossref_service import verify_title
from app.services.semantic_scholar_service import (
    search_semantic_scholar,
)
from app.services.openalex_service import (
    search_openalex,
)


def retrieve_candidates(title):
    """
    Retrieve candidate papers from multiple scholarly databases.

    Returns one merged candidate list.
    """

    if not title:
        return []

    crossref = verify_title(title)

    semantic = search_semantic_scholar(title)

    openalex = search_openalex(title)

    merged = []

    seen = set()

    for paper in crossref + semantic + openalex:

        if not paper:
            continue

        key = (
            (paper.get("title") or "")
            .lower()
            .strip()
        )

        if key in seen:
            continue

        seen.add(key)

        merged.append(paper)

    return merged