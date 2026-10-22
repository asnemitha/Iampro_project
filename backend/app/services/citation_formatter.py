from app.services.metadata_normalizer import canonicalize_verified_metadata


def format_ieee(metadata):
    """
    Convert verified metadata into IEEE-style citation with a single canonical year.
    """

    if metadata is None:
        return None

    # Ensure metadata is canonicalized (single year, clean venue and DOI)
    norm = canonicalize_verified_metadata(metadata)
    if norm:
        metadata = norm

    authors = metadata.get("authors", [])

    if len(authors) == 0:
        author_text = "Unknown Author"

    elif len(authors) == 1:
        author_text = authors[0]

    elif len(authors) == 2:
        author_text = f"{authors[0]} and {authors[1]}"

    else:
        author_text = ", ".join(authors[:-1]) + ", and " + authors[-1]

    parts = [author_text, f'"{metadata.get("title", "")}"']
    if metadata.get("venue"):
        parts.append(metadata["venue"])
    if metadata.get("year"):
        parts.append(str(metadata["year"]))
    if metadata.get("doi"):
        parts.append(f'DOI: {metadata["doi"]}')

    return ", ".join(parts)