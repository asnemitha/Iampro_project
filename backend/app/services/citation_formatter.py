def format_ieee(metadata):
    """
    Convert verified metadata into IEEE-style citation.
    """

    if metadata is None:
        return None

    authors = metadata.get("authors", [])

    if len(authors) == 0:
        author_text = "Unknown Author"

    elif len(authors) == 1:
        author_text = authors[0]

    elif len(authors) == 2:
        author_text = f"{authors[0]} and {authors[1]}"

    else:
        author_text = ", ".join(authors[:-1]) + ", and " + authors[-1]

    citation = (
        f'{author_text}, '
        f'"{metadata["title"]}", '
        f'{metadata["venue"]}, '
        f'{metadata["year"]}, '
        f'DOI: {metadata["doi"]}'
    )

    return citation