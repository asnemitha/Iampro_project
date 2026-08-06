import re


def normalize_text(text: str):
    """
    Normalize text for comparison.
    """

    if not text:
        return ""

    text = text.lower()

    text = re.sub(r"[^a-z0-9 ]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_title(title: str):
    """
    Normalize paper title.
    """

    return normalize_text(title)


def normalize_author(author: str):
    """
    Normalize a single author name.
    """

    if not author:
        return ""

    author = normalize_text(author)

    # Remove titles
    author = re.sub(r"\b(dr|prof|mr|mrs|ms)\b", "", author)

    author = re.sub(r"\s+", " ", author)

    return author.strip()


def normalize_authors(authors):
    """
    Normalize list of authors.
    """

    if not authors:
        return []

    return [
        normalize_author(author)
        for author in authors
        if author
    ]


def normalize_venue(venue: str):
    """
    Normalize publication venue.
    """

    if not venue:
        return ""

    venue = normalize_text(venue)

    replacements = {
        "proceedings of": "",
        "international": "",
        "conference on": "",
        "ieee": "",
        "acm": "",
        "journal of": "",
        "transactions on": "",
        "the": "",
    }

    for old, new in replacements.items():
        venue = venue.replace(old, new)

    venue = re.sub(r"\s+", " ", venue)

    return venue.strip()


def normalize_doi(doi: str):
    """
    Normalize DOI.
    """

    if not doi:
        return None

    return doi.strip().lower()


def normalize_metadata(metadata: dict):
    """
    Normalize an entire metadata dictionary.
    """

    if metadata is None:
        return None

    return {
        "title": normalize_title(metadata.get("title")),
        "authors": normalize_authors(metadata.get("authors", [])),
        "venue": normalize_venue(metadata.get("venue")),
        "year": metadata.get("year"),
        "doi": normalize_doi(metadata.get("doi")),
    }