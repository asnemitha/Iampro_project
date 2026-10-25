import re
from typing import Optional, List, Dict, Any

from app.services.verification_pipeline import verify_response
from app.services.metadata_normalizer import canonicalize_verified_metadata
from app.services.citation_formatter import format_ieee
from app.services.claim_verification_service import (
    extract_claim_for_citation,
    verify_claim_support,
)


def replace_citation_in_text(full_text: str, old_citation: str, new_citation: str) -> str:
    """
    Robustly replace old_citation in full_text even when whitespace, line breaks,
    or trailing spaces differ slightly between extracted citation text and full_text.
    """
    if not full_text or not old_citation:
        return full_text

    # 1. Exact string replacement
    if old_citation in full_text:
        return full_text.replace(old_citation, new_citation, 1)

    # Normalize line endings
    norm_full = full_text.replace("\r\n", "\n")
    norm_old = old_citation.replace("\r\n", "\n")

    if norm_old in norm_full:
        return norm_full.replace(norm_old, new_citation, 1)

    # 2. Line-by-line stripped matching (allowing flexible intra-line whitespace)
    lines = [l.strip() for l in norm_old.split("\n") if l.strip()]
    if not lines:
        return full_text

    pattern_parts = [re.escape(l) for l in lines]
    # Join with flexible whitespace and optional line breaks
    pattern = r"[ \t]*\n[ \t]*".join(pattern_parts)
    match = re.search(pattern, norm_full, flags=re.IGNORECASE)
    if match:
        return norm_full[:match.start()] + new_citation + norm_full[match.end():]

    # 3. Fallback: match by citation header line and find end of block
    first_line = lines[0]
    first_match = re.search(r"^[ \t]*" + re.escape(first_line), norm_full, flags=re.MULTILINE | re.IGNORECASE)
    if first_match:
        start_pos = first_match.start()
        rest = norm_full[start_pos:]
        # Find next numbered citation or double newline or end of string
        block_match = re.search(r"\n\s*(?=\d+[\.\)]|\[\d+\]|Paper\s*\d+:?|\Z)", rest[len(first_line):])
        if block_match:
            end_pos = start_pos + len(first_line) + block_match.start()
        else:
            end_pos = len(norm_full)
        return norm_full[:start_pos] + new_citation + norm_full[end_pos:]

    return full_text


def build_replacement_citation(original_citation: str, canonical_meta: dict) -> str:
    """
    Format a replacement citation matching the structural style of the original citation.
    """
    if not canonical_meta:
        return original_citation

    orig = original_citation.strip()
    lines = [l.strip() for l in orig.split("\n") if l.strip()]
    first_line = lines[0] if lines else ""

    # Check for prefix numbering (e.g. "1. ", "[1] ", "Paper 1: ")
    prefix_match = re.match(r"^(\[?\d+\]?[\.\)]?\s*|Paper\s*\d+:?\s*)", first_line, re.IGNORECASE)
    prefix = prefix_match.group(1) if prefix_match else ""

    # Check if structured key-value style (Authors:, Year:, Venue:, DOI:)
    has_authors_field = any(re.match(r"^Authors?\s*:", l, re.IGNORECASE) for l in lines)
    has_year_field = any(re.match(r"^Year\s*:", l, re.IGNORECASE) for l in lines)
    has_venue_field = any(re.match(r"^Venue\s*:", l, re.IGNORECASE) for l in lines)
    has_doi_field = any(re.match(r"^DOI\s*:", l, re.IGNORECASE) for l in lines)

    authors_list = canonical_meta.get("authors") or []
    if isinstance(authors_list, str):
        authors_list = [a.strip() for a in authors_list.split(";") if a.strip()]
    authors_str = ", ".join(authors_list) if authors_list else "Unknown Author"
    title_str = canonical_meta.get("title") or "Unknown Title"
    year_str = str(canonical_meta.get("year")) if canonical_meta.get("year") else ""
    venue_str = canonical_meta.get("venue") or ""
    doi_str = canonical_meta.get("doi") or ""

    # Preserve any summary/context lines from the original citation
    summary_lines = [
        l for l in lines
        if re.match(r"^(?:Summary|Context|Contribution|Claim)\s*:", l, re.IGNORECASE)
    ]

    if has_authors_field or has_year_field or has_venue_field or has_doi_field:
        rep_lines = []
        clean_prefix = prefix.strip()
        if clean_prefix and not (clean_prefix.endswith(".") or clean_prefix.endswith(":") or clean_prefix.endswith("]")):
            clean_prefix += "."

        if clean_prefix:
            rep_lines.append(f"{clean_prefix} {title_str}")
        else:
            rep_lines.append(f"Title: {title_str}")

        rep_lines.append(f"Authors: {authors_str}")
        if year_str:
            rep_lines.append(f"Year: {year_str}")
        if venue_str:
            rep_lines.append(f"Venue: {venue_str}")
        if doi_str:
            rep_lines.append(f"DOI: {doi_str}")

        for sl in summary_lines:
            rep_lines.append(sl)

        return "\n".join(rep_lines)

    # Bracketed IEEE style: [1]
    if prefix.startswith("["):
        clean_prefix = prefix.strip()
        ieee_text = format_ieee(canonical_meta)
        return f"{clean_prefix} {ieee_text}"

    # Default to IEEE format with prefix
    ieee_text = format_ieee(canonical_meta)
    if prefix:
        return f"{prefix}{ieee_text}"
    return ieee_text


def build_qualified_unverified_citation(original_citation: str, citation_result: dict) -> str:
    """
    Transparently annotate an unverified or fabricated citation in the response.
    Never invents replacement metadata or silently drops content.
    """
    orig = original_citation.strip()
    if "[UNVERIFIED REFERENCE" in orig:
        return orig

    reason = "Referenced paper could not be verified in Crossref, Semantic Scholar, or OpenAlex"
    if citation_result.get("hallucination_type") == "Unverified / Provider Outage":
        reason = "External scholarly APIs were unreachable during verification"

    warning_text = f" [UNVERIFIED REFERENCE: {reason}. This citation may be hallucinated or incorrect.]"

    lines = orig.split("\n")
    if len(lines) > 1:
        return f"{orig}\nNote:{warning_text}"
    return f"{orig}{warning_text}"


def search_replacement_paper(claim: str, user_prompt: str = None) -> Optional[dict]:
    """
    Attempt to find genuine scholarly literature relevant to an unsupported claim or topic.
    Returns candidate paper dict ONLY if a credible, highly relevant source is found; otherwise None.
    Never invents or substitutes unrelated papers.
    """
    if not claim:
        return None

    from app.services.claim_verification_service import _tokenize
    from rapidfuzz import fuzz

    claim_tokens = _tokenize(claim)
    if not claim_tokens or len(claim_tokens) < 2:
        return None

    query = " ".join(list(claim_tokens)[:6])
    if not query or len(query) < 5:
        return None

    try:
        from app.services.multi_source_retriever import retrieve_candidates
        candidates = retrieve_candidates(query)
        if not candidates:
            return None

        # Must have high semantic relevance to the claim or prompt (at least 50% token overlap and fuzz >= 70)
        for cand in candidates[:5]:
            cand_title = cand.get("title") or ""
            if not cand_title or not cand.get("authors") or not (cand.get("doi") or cand.get("venue")):
                continue

            cand_tokens = _tokenize(cand_title)
            overlap = claim_tokens.intersection(cand_tokens)
            overlap_ratio = len(overlap) / len(claim_tokens) if claim_tokens else 0
            fuzz_score = fuzz.token_set_ratio(claim, cand_title)

            # High semantic relevance requirement:
            # Overlap must be at least 50% and fuzz score >= 70
            if overlap_ratio >= 0.50 and fuzz_score >= 70:
                return cand
    except Exception:
        return None

    return None


def correct_and_reverify_response(
    response_text: str,
    user_prompt: str = None,
    max_iterations: int = 2,
    verifier=None
) -> Dict[str, Any]:
    """
    Closed-loop verification, correction, and re-verification workflow.

    Workflow:
    1. Extract and verify every citation in response_text using full Author+Venue validation.
    2. Check claim-to-source support using retrieved evidence.
    3. Detect metadata discrepancies, fabricated references, and unsupported claims.
    4. Automatically apply evidence-based corrections or transparent qualifications.
    5. Re-verify the revised response in subsequent iterations up to max_iterations.
    6. Return comprehensive audit trail, metrics, and final trustworthy response.
    """
    if verifier is None:
        verifier = verify_response

    current_text = (response_text or "").replace("\r\n", "\n").strip()
    original_text = (response_text or "").replace("\r\n", "\n").strip()

    if not current_text:
        return {
            "original_response": "",
            "final_response": "",
            "llm_response": "",
            "initial_citation_analysis": [],
            "final_citation_analysis": [],
            "applied_corrections": [],
            "verification_summary": {
                "final_status": "verified",
                "total_citations": 0,
                "verified_count": 0,
                "corrected_and_verified_count": 0,
                "unresolved_count": 0,
                "iterations_run": 0,
                "limitations": "No text provided for citation verification.",
            },
            "audit_trail": [],
        }

    applied_corrections: List[Dict[str, Any]] = []
    audit_trail: List[Dict[str, Any]] = []
    initial_citation_analysis: List[Dict[str, Any]] = []
    final_citation_analysis: List[Dict[str, Any]] = []

    iterations_run = 0

    for iteration in range(1, max_iterations + 1):
        iterations_run = iteration

        # 1. Run citation verification on the current text (ensuring full author and venue validation)
        try:
            results = verifier(
                current_text,
                use_author_fix=True,
                use_venue_fix=True,
                user_prompt=user_prompt
            )
        except TypeError:
            # Fallback if verifier mock does not take use_author_fix keyword argument
            results = verifier(current_text, user_prompt=user_prompt)

        # 2. Attach claim-to-source verification for each citation
        for r in results:
            cit_text = r.get("citation", "")
            claim_text = extract_claim_for_citation(current_text, cit_text)
            claim_result = verify_claim_support(claim_text, r)
            r["claim_verification"] = claim_result

        if iteration == 1:
            initial_citation_analysis = list(results)

        final_citation_analysis = list(results)

        # 3. Identify all discrepancies
        discrepancies = []
        for r in results:
            errors = list(r.get("metadata_errors", []))
            paper_exists = r.get("paper_exists")
            citation_accurate = r.get("citation_accurate")
            claim_status = r.get("claim_verification", {}).get("status")

            has_issue = (
                not citation_accurate
                or paper_exists is False
                or paper_exists is None
                or claim_status == "unsupported_claim"
                or bool(errors)
            )
            if has_issue:
                discrepancies.append({
                    "citation": r.get("citation"),
                    "errors": errors,
                    "paper_exists": paper_exists,
                    "hallucination_type": r.get("hallucination_type"),
                    "claim_status": claim_status,
                })

        audit_trail.append({
            "iteration": iteration,
            "text_analyzed": current_text,
            "total_citations": len(results),
            "discrepancies_detected": discrepancies,
            "discrepancy_count": len(discrepancies),
        })

        # If no discrepancies remain, response is fully verified
        if len(discrepancies) == 0:
            break

        # If this is the final allowed iteration, stop
        if iteration >= max_iterations:
            break

        # 4. Attempt corrections on current_text
        revised_text = current_text
        step_corrections = []

        for r in results:
            cit_str = r.get("citation", "")
            if not cit_str:
                continue

            errors = list(r.get("metadata_errors", []))
            paper_exists = r.get("paper_exists")
            citation_accurate = r.get("citation_accurate")
            claim_status = r.get("claim_verification", {}).get("status")

            replacement_str = None
            correction_type = None
            explanation = ""

            # Establish whether the matched candidate is genuinely the intended publication
            from app.services.similarity_service import compare_titles, compare_authors
            parsed_meta = r.get("parsed") or {}
            c_title = parsed_meta.get("title")
            m_title = r.get("matched_title")
            c_authors = parsed_meta.get("authors") or []
            m_authors = r.get("matched_authors") or []

            title_sim = compare_titles(c_title, m_title)["score"] if (c_title and m_title) else 100.0
            author_sim = compare_authors(c_authors, m_authors) if (c_authors and m_authors) else 100.0

            # Reliable identification check:
            # Matched paper must be genuinely the same publication as claimed:
            # Distinguish clearly between:
            # - metadata correction of the SAME paper (e.g. fixing a typo in title or an incorrect DOI for a real paper), and
            # - an entirely different paper (which must NEVER be substituted to make a fabricated citation appear verified).
            authors_conflict = bool(
                c_authors and m_authors and author_sim < 40.0 and not r.get("doi_match")
            )
            is_reliable_intended_publication = (
                paper_exists is True
                and (
                    (title_sim >= 90.0)
                    or (not authors_conflict and r.get("doi_match") is True and (title_sim >= 50.0 or author_sim >= 50.0))
                    or (not authors_conflict and title_sim >= 75.0 and (not c_authors or author_sim >= 50.0))
                    or (not authors_conflict and title_sim >= 70.0 and author_sim >= 60.0 and (r.get("year_match") or r.get("venue_match")))
                )
            )

            # Case A: Paper exists and is reliably the intended publication, but metadata has discrepancies
            if is_reliable_intended_publication and (not citation_accurate or errors):
                canonical_meta = canonicalize_verified_metadata({
                    "title": r.get("matched_title"),
                    "authors": r.get("matched_authors"),
                    "venue": r.get("matched_venue"),
                    "year": r.get("matched_year"),
                    "doi": r.get("matched_doi"),
                    "abstract": r.get("matched_abstract"),
                    "source": r.get("provenance", {}).get("primary_source") if r.get("provenance") else "Crossref",
                    "provenance": r.get("provenance"),
                }, parsed_citation=parsed_meta)
                replacement_str = build_replacement_citation(cit_str, canonical_meta)
                correction_type = "metadata_correction"
                explanation = (
                    f"Corrected metadata discrepancies: {', '.join(errors) if errors else 'canonicalized fields'} "
                    f"using authoritative Crossref/DataCite records."
                )

            # Case B: Paper does not exist OR candidate is not reliably the intended publication
            # Fabricated or unverified citations must NEVER be substituted with unrelated papers.
            elif (paper_exists is False) or (paper_exists is None) or (not is_reliable_intended_publication):
                replacement_str = build_qualified_unverified_citation(cit_str, r)
                correction_type = "transparent_qualification"
                explanation = "Paper could not be verified in scholarly databases. Explicitly marked as an unverified reference."

            # Case C: Claim-to-source mismatch (paper exists and is intended publication, but does not support claim)
            elif claim_status == "unsupported_claim":
                replacement_str = f"{cit_str}\n[Warning: Claim-to-source mismatch. The cited paper does not substantiate this claim.]"
                correction_type = "claim_mismatch_annotation"
                explanation = "Flagged claim-to-source mismatch where the cited reference does not support the stated passage."

            # Apply replacement to revised_text using robust matching
            if replacement_str and replacement_str != cit_str:
                new_text = replace_citation_in_text(revised_text, cit_str, replacement_str)
                if new_text != revised_text:
                    revised_text = new_text
                    corr_entry = {
                        "original_citation": cit_str,
                        "corrected_citation": replacement_str,
                        "correction_type": correction_type,
                        "explanation": explanation,
                        "iteration": iteration,
                        "verified_in_next_step": False,
                    }
                    applied_corrections.append(corr_entry)
                    step_corrections.append(corr_entry)

        # If no replacements were applied, further iterations cannot change anything
        if revised_text == current_text or not step_corrections:
            break

        current_text = revised_text

    # Final pass: Determine whether applied corrections were verified in final_citation_analysis
    for corr in applied_corrections:
        corr_cit = corr["corrected_citation"]
        corr_type = corr.get("correction_type")
        if corr_type in ("transparent_qualification", "claim_mismatch_annotation"):
            # Transparent qualifications and claim mismatch annotations are deliberate unverified annotations, not verified citations
            corr["verified_in_next_step"] = False
            continue

        for fr in final_citation_analysis:
            fr_cit = fr.get("citation", "")
            claim_stat = fr.get("claim_verification", {}).get("status")
            if (
                fr.get("paper_exists") is True
                and fr.get("citation_accurate") is True
                and claim_stat != "unsupported_claim"
                and (
                    fr_cit == corr_cit
                    or (fr.get("matched_title") and fr.get("matched_title").lower() in corr_cit.lower())
                )
            ):
                corr["verified_in_next_step"] = True
                break

    # Calculate summary metrics based strictly on final_citation_analysis
    total_citations = len(final_citation_analysis)
    verified_count = sum(
        1 for r in final_citation_analysis
        if r.get("paper_exists") is True
        and r.get("citation_accurate") is True
        and r.get("claim_verification", {}).get("status") in ["supported", "insufficient_evidence"]
    )
    corrected_and_verified_count = sum(
        1 for c in applied_corrections if c.get("verified_in_next_step")
    )
    unresolved_count = sum(
        1 for r in final_citation_analysis
        if r.get("paper_exists") is False
        or r.get("paper_exists") is None
        or not r.get("citation_accurate")
        or r.get("claim_verification", {}).get("status") == "unsupported_claim"
        or r.get("hallucination_type") in ["Fabricated Citation", "Unverified / Provider Outage"]
    )

    # Determine final truthful verification status
    if total_citations == 0:
        final_status = "verified"
        limitations = "No citations detected in this response."
    elif (
        all(r.get("hallucination_type") == "Unverified / Provider Outage" for r in final_citation_analysis)
        or (any(r.get("hallucination_type") == "Unverified / Provider Outage" or r.get("api_status") == "OUTAGE" for r in final_citation_analysis) and verified_count == 0)
    ):
        final_status = "unverified"
        limitations = (
            "Scholarly metadata registries (Crossref, Semantic Scholar, OpenAlex, DataCite) were unreachable or returned rate limits; "
            "citations could not be verified."
        )
    elif unresolved_count == 0:
        final_status = "verified"
        limitations = (
            "All citations match authoritative registry metadata with zero unresolved discrepancies. "
            "Where full-text is not indexed in public registries, verification is based on bibliographic and abstract records."
        )
    elif verified_count > 0 and unresolved_count > 0:
        final_status = "partially_verified"
        limitations = (
            f"{unresolved_count} citation(s) remain unresolved or qualified. "
            "Do not cite unverified references in production academic publications."
        )
    elif len(applied_corrections) > 0 and unresolved_count > 0:
        final_status = "correction_failed"
        limitations = (
            "Automated correction attempts were unable to resolve all citation discrepancies against authoritative registries."
        )
    else:
        final_status = "unverified"
        limitations = (
            "Available evidence in Crossref, Semantic Scholar, and OpenAlex is insufficient to substantiate the citations."
        )

    verification_summary = {
        "final_status": final_status,
        "total_citations": total_citations,
        "verified_count": verified_count,
        "corrected_and_verified_count": corrected_and_verified_count,
        "unresolved_count": unresolved_count,
        "iterations_run": iterations_run,
        "limitations": limitations,
    }

    return {
        "original_response": original_text,
        "final_response": current_text,
        "llm_response": current_text,
        "initial_citation_analysis": initial_citation_analysis,
        "final_citation_analysis": final_citation_analysis,
        "applied_corrections": applied_corrections,
        "verification_summary": verification_summary,
        "audit_trail": audit_trail,
    }
