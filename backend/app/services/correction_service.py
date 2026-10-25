import re
from typing import Optional, List, Dict, Any

from app.services.verification_pipeline import verify_response
from app.services.metadata_normalizer import canonicalize_verified_metadata
from app.services.citation_formatter import format_ieee
from app.services.claim_verification_service import (
    extract_claim_for_citation,
    verify_claim_support,
)


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
    Returns candidate paper dict only if a credible source is found; otherwise None.
    """
    if not claim:
        return None

    from app.services.claim_verification_service import _tokenize
    tokens = list(_tokenize(claim))[:6]
    query = " ".join(tokens)
    if not query or len(query) < 4:
        return None

    try:
        from app.services.multi_source_retriever import retrieve_candidates
        candidates = retrieve_candidates(query)
        if not candidates:
            return None

        # Look for a candidate with high credibility (title + authors + venue/doi)
        for cand in candidates[:5]:
            if cand.get("title") and cand.get("authors") and (cand.get("doi") or cand.get("venue")):
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
    1. Extract and verify every citation in response_text.
    2. Check claim-to-source support using retrieved evidence.
    3. Detect metadata discrepancies and claim mismatches.
    4. Automatically apply evidence-based corrections or transparent qualifications.
    5. Re-verify the revised response in subsequent iterations up to max_iterations.
    6. Return comprehensive audit trail, metrics, and final trustworthy response.
    """
    if verifier is None:
        verifier = verify_response

    current_text = (response_text or "").strip()
    original_text = current_text

    if not current_text:
        return {
            "original_response": "",
            "final_response": "",
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

        # 1. Run citation verification on the current text
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

        # If no discrepancies remain, response is clean
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
            if not cit_str or cit_str not in revised_text:
                continue

            errors = list(r.get("metadata_errors", []))
            paper_exists = r.get("paper_exists")
            citation_accurate = r.get("citation_accurate")
            claim_status = r.get("claim_verification", {}).get("status")

            replacement_str = None
            correction_type = None
            explanation = ""

            # Case A: Paper exists, but metadata has discrepancies (wrong authors, year, venue, DOI)
            if paper_exists and (not citation_accurate or errors):
                canonical_meta = canonicalize_verified_metadata({
                    "title": r.get("matched_title"),
                    "authors": r.get("matched_authors"),
                    "venue": r.get("matched_venue"),
                    "year": r.get("matched_year"),
                    "doi": r.get("matched_doi"),
                    "abstract": r.get("matched_abstract"),
                })
                replacement_str = build_replacement_citation(cit_str, canonical_meta)
                correction_type = "metadata_correction"
                explanation = (
                    f"Corrected metadata discrepancies: {', '.join(errors) if errors else 'canonicalized fields'} "
                    f"using authoritative Crossref/DataCite records."
                )

            # Case B: Paper does not exist (Fabricated / Not Found)
            elif paper_exists is False:
                claim = r.get("claim_verification", {}).get("claim")
                rep_paper = search_replacement_paper(claim, user_prompt)
                if rep_paper and rep_paper.get("title"):
                    canonical_rep = canonicalize_verified_metadata(rep_paper)
                    replacement_str = build_replacement_citation(cit_str, canonical_rep)
                    correction_type = "source_substitution"
                    explanation = f"Substituted unverified reference with genuine verified paper: '{canonical_rep.get('title')}'."
                else:
                    replacement_str = build_qualified_unverified_citation(cit_str, r)
                    correction_type = "transparent_qualification"
                    explanation = "Paper could not be verified in scholarly databases. Explicitly marked as an unverified reference."

            # Case C: Claim-to-source mismatch
            elif claim_status == "unsupported_claim":
                replacement_str = f"{cit_str}\n[Warning: Claim-to-source mismatch. The cited paper does not substantiate this claim.]"
                correction_type = "claim_mismatch_annotation"
                explanation = "Flagged claim-to-source mismatch where the cited reference does not support the stated passage."

            # Apply replacement to revised_text
            if replacement_str and replacement_str != cit_str:
                revised_text = revised_text.replace(cit_str, replacement_str, 1)
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
        for fr in final_citation_analysis:
            fr_cit = fr.get("citation", "")
            if (
                fr.get("paper_exists") is True
                and fr.get("citation_accurate") is True
                and (
                    fr_cit == corr_cit
                    or (fr.get("matched_title") and fr.get("matched_title").lower() in corr_cit.lower())
                )
            ):
                corr["verified_in_next_step"] = True
                break

    # Calculate summary metrics
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

    # Determine final verification status
    if total_citations == 0:
        final_status = "verified"
        limitations = "No citations detected in this response."
    elif all(r.get("hallucination_type") == "Unverified / Provider Outage" for r in final_citation_analysis):
        final_status = "unverified"
        limitations = (
            "Scholarly metadata registries (Crossref, Semantic Scholar, OpenAlex) were unreachable or returned rate limits; "
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
