import { useState } from "react";

export default function CitationTable({
  citations = [],
  initialCitations = [],
  appliedCorrections = [],
}) {
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [copiedRawIndex, setCopiedRawIndex] = useState(null);
  const [filter, setFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState("natural");
  const [auditStage, setAuditStage] = useState("final"); // "final" or "submitted"

  const hasCorrections = Boolean(appliedCorrections && appliedCorrections.length > 0 && initialCitations && initialCitations.length > 0);
  const activeCitations = (hasCorrections && auditStage === "submitted") ? initialCitations : citations;

  if (!activeCitations || activeCitations.length === 0) {
    return (
      <div className="bg-white dark:bg-[#1F1F24] border-2 border-black rounded-xl shadow-[4px_4px_0px_#111] p-6 text-center">
        <p className="font-mono text-sm text-neutral-600 dark:text-neutral-400">
          No citations were detected in the response.
        </p>
      </div>
    );
  }

  const handleCopyCitation = (text, index) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleCopyRaw = (text, index) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedRawIndex(index);
    setTimeout(() => setCopiedRawIndex(null), 2000);
  };

  // Classify citations for filtering
  const getCitationType = (c) => {
    const score = typeof c.hallucination_score === "number" ? c.hallucination_score : 0;
    if (c.paper_exists === false || score > 50) return "hallucinated";
    if (score > 20 || !c.citation_accurate || (c.metadata_errors && c.metadata_errors.length > 0)) return "review";
    return "verified";
  };

  const counts = {
    all: activeCitations.length,
    verified: activeCitations.filter((c) => getCitationType(c) === "verified").length,
    review: activeCitations.filter((c) => getCitationType(c) === "review").length,
    hallucinated: activeCitations.filter((c) => getCitationType(c) === "hallucinated").length,
  };

  let displayedCitations = activeCitations.filter((c) => {
    if (filter === "all") return true;
    return getCitationType(c) === filter;
  });

  if (sortOrder === "risk_desc") {
    displayedCitations = [...displayedCitations].sort(
      (a, b) => (b.hallucination_score || 0) - (a.hallucination_score || 0)
    );
  } else if (sortOrder === "risk_asc") {
    displayedCitations = [...displayedCitations].sort(
      (a, b) => (a.hallucination_score || 0) - (b.hallucination_score || 0)
    );
  }

  return (
    <div className="space-y-5">
      {/* AUDIT STAGE TOGGLE (Shown when closed-loop corrections were performed) */}
      {hasCorrections && (
        <div className="bg-white dark:bg-[#1F1F24] border-2 border-black rounded-xl p-3 shadow-[3px_3px_0px_#111] flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-lg bg-[#EBB13E] border border-black font-mono text-xs font-black flex items-center justify-center text-black shadow-[1px_1px_0px_#111]">
              ⚖
            </span>
            <span className="font-mono text-xs font-black uppercase tracking-wider text-neutral-800 dark:text-neutral-200">
              CITATION AUDIT STAGE:
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setAuditStage("final")}
              className={`px-3 py-1.5 rounded-xl border-2 border-black font-mono text-xs font-black tracking-wide shadow-btn transition-all cursor-pointer flex items-center gap-1.5 ${
                auditStage === "final"
                  ? "bg-[#2563EB] text-white shadow-[2px_2px_0px_#111]"
                  : "bg-white dark:bg-[#27272a] text-neutral-800 dark:text-neutral-200 hover:text-black dark:hover:text-white"
              }`}
            >
              <span>✓</span>
              <span>Final Re-verified Citations ({citations.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setAuditStage("submitted")}
              className={`px-3 py-1.5 rounded-xl border-2 border-black font-mono text-xs font-black tracking-wide shadow-btn transition-all cursor-pointer flex items-center gap-1.5 ${
                auditStage === "submitted"
                  ? "bg-[#EBB13E] text-black shadow-[2px_2px_0px_#111]"
                  : "bg-white dark:bg-[#27272a] text-neutral-800 dark:text-neutral-200 hover:text-black dark:hover:text-white"
              }`}
            >
              <span>⏮</span>
              <span>Original Submitted Citations (Discrepancy Audit) ({initialCitations.length})</span>
            </button>
          </div>
        </div>
      )}

      {/* Stage Explanatory Banner when viewing submitted audit */}
      {hasCorrections && auditStage === "submitted" && (
        <div className="p-3.5 bg-[#FEF3C7] dark:bg-[#27272a] border-2 border-black rounded-xl text-[#92400E] dark:text-amber-200 font-mono text-xs shadow-[2px_2px_0px_#111] flex items-center gap-2">
          <span className="text-base">⚠️</span>
          <span>
            <b>Original Submitted Metadata Audit:</b> Below are the uncorrected raw citations extracted from the initial input, highlighting the specific bibliographic discrepancies detected before closed-loop rectification.
          </span>
        </div>
      )}

      {/* FILTER & SORT BAR */}
      <div className="bg-white dark:bg-[#1F1F24] border-2 border-black rounded-xl p-3 shadow-[3px_3px_0px_#111] flex flex-wrap items-center justify-between gap-3">
        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs font-black uppercase tracking-wider text-neutral-600 dark:text-neutral-400 mr-1">
            FILTER:
          </span>

          <button
            type="button"
            onClick={() => setFilter("all")}
            className={`px-3 py-1 rounded-xl border-2 border-black font-mono text-xs font-black tracking-wide shadow-btn transition-all cursor-pointer ${
              filter === "all"
                ? "bg-[#EBB13E] text-black shadow-[2px_2px_0px_#111]"
                : "bg-white dark:bg-[#27272a] text-neutral-800 dark:text-neutral-200"
            }`}
          >
            All ({counts.all})
          </button>

          <button
            type="button"
            onClick={() => setFilter("verified")}
            className={`px-3 py-1 rounded-xl border-2 border-black font-mono text-xs font-black tracking-wide shadow-btn transition-all cursor-pointer ${
              filter === "verified"
                ? "bg-[#2563EB] text-white shadow-[2px_2px_0px_#111]"
                : "bg-white dark:bg-[#27272a] text-neutral-800 dark:text-neutral-200"
            }`}
          >
            Verified ({counts.verified})
          </button>

          <button
            type="button"
            onClick={() => setFilter("review")}
            className={`px-3 py-1 rounded-xl border-2 border-black font-mono text-xs font-black tracking-wide shadow-btn transition-all cursor-pointer ${
              filter === "review"
                ? "bg-[#EBB13E] text-black shadow-[2px_2px_0px_#111]"
                : "bg-white dark:bg-[#27272a] text-neutral-800 dark:text-neutral-200"
            }`}
          >
            Review ({counts.review})
          </button>

          <button
            type="button"
            onClick={() => setFilter("hallucinated")}
            className={`px-3 py-1 rounded-xl border-2 border-black font-mono text-xs font-black tracking-wide shadow-btn transition-all cursor-pointer ${
              filter === "hallucinated"
                ? "bg-[#E0453A] text-white shadow-[2px_2px_0px_#111]"
                : "bg-white dark:bg-[#27272a] text-neutral-800 dark:text-neutral-200"
            }`}
          >
            Hallucinated ({counts.hallucinated})
          </button>
        </div>

        {/* Sort Dropdown */}
        <div className="flex items-center gap-1.5 font-mono text-xs">
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
            className="bg-white dark:bg-[#27272a] text-neutral-900 dark:text-neutral-100 border-2 border-black rounded-xl px-2.5 py-1 font-mono text-xs font-bold shadow-[2px_2px_0px_#111] cursor-pointer focus:outline-none"
          >
            <option value="natural">↑↓ Natural Order</option>
            <option value="risk_desc">Risk: Highest First</option>
            <option value="risk_asc">Risk: Lowest First</option>
          </select>
        </div>
      </div>

      {/* CITATION CARDS */}
      {displayedCitations.map((citation, index) => {
        const score = typeof citation.hallucination_score === "number" ? citation.hallucination_score : 0;
        const cType = getCitationType(citation);

        // Subtitle generation
        let subtitle = "Metadata Hallucination • Paper Exists but Citation Contains Errors";
        if (auditStage === "submitted") {
          subtitle = cType === "verified"
            ? "Submitted Citation • Verified Accurate"
            : cType === "hallucinated"
            ? "Submitted Citation • Paper Not Found in Registries"
            : "Submitted Citation • Bibliographic Errors Detected";
        } else {
          if (cType === "verified") {
            subtitle = "Genuine Citation • Authoritative Bibliographic Record Matched";
          } else if (cType === "hallucinated") {
            subtitle = "Plausible Fabricated Citation • Paper Not Found in Scholarly Registries";
          }
        }

        // Top-right badge
        let mainBadgeLabel = "FLAGGED FOR REVIEW";
        let mainBadgeClass = "bg-[#EBB13E] text-black border-black";
        if (cType === "hallucinated") {
          mainBadgeLabel = "FLAGGED FOR REVIEW";
          mainBadgeClass = "bg-[#E0453A] text-white border-black";
        } else if (cType === "verified") {
          mainBadgeLabel = "VERIFIED ACCURATE";
          mainBadgeClass = "bg-[#2563EB] text-white border-black";
        }

        // Field checks calculations
        // 1. DOI: Verified ONLY if provided and genuinely belongs to the authoritative matched publication
        const doiProvided = Boolean(citation.parsed?.doi);
        const doiMismatch = (
          citation.doi_match === false ||
          citation.metadata_errors?.some((e) => e.toLowerCase().includes("doi")) ||
          citation.reason?.some((r) => r.toLowerCase().includes("doi differs") || r.toLowerCase().includes("doi does not belong"))
        );
        const doiMatch = citation.doi_match === true && !doiMismatch;

        let doiStatus = "not_provided";
        if (doiProvided) {
          doiStatus = doiMatch ? "verified" : "mismatch";
        }

        // 2. Authors
        const authorsProvided = Boolean(citation.parsed?.authors && citation.parsed.authors.length > 0);
        const authorMismatch = (
          citation.metadata_errors?.some((e) => e.toLowerCase().includes("author")) ||
          citation.reason?.some((r) => r.toLowerCase().includes("authors differ") || r.toLowerCase().includes("author metadata missing")) ||
          (typeof citation.author_similarity === "number" && citation.author_similarity < 70 && authorsProvided)
        );
        const authorMatch = !authorMismatch && (
          citation.author_similarity >= 70 ||
          citation.citation_accurate === true ||
          citation.reason?.some((r) => r.toLowerCase() === "authors match." || r.toLowerCase() === "authors match")
        );

        let authorStatus = "not_provided";
        if (authorsProvided) {
          authorStatus = authorMatch ? "verified" : "corrupted";
        }

        // 3. Venue
        const venueProvided = Boolean(citation.parsed?.venue);
        const venueMismatch = (
          citation.metadata_errors?.some((e) => e.toLowerCase().includes("venue")) ||
          citation.reason?.some((r) => r.toLowerCase().includes("venue differs")) ||
          citation.venue_match === false
        );
        const venueMatch = !venueMismatch && (
          citation.venue_match === true ||
          citation.citation_accurate === true ||
          citation.reason?.some((r) => r.toLowerCase() === "venue matches." || r.toLowerCase() === "venue matches")
        );

        let venueStatus = "not_provided";
        if (venueProvided) {
          venueStatus = venueMatch ? "verified" : "inaccurate";
        }

        // 4. Year
        const yearProvided = Boolean(citation.parsed?.year);
        const yearMismatch = (
          citation.metadata_errors?.some((e) => e.toLowerCase().includes("year")) ||
          citation.reason?.some((r) => r.toLowerCase().includes("publication year differs") || r.toLowerCase().includes("publication year missing")) ||
          citation.year_match === false
        );
        const yearMatch = !yearMismatch && (
          citation.year_match === true ||
          citation.citation_accurate === true ||
          citation.reason?.some((r) => r.toLowerCase() === "publication year matches." || r.toLowerCase() === "publication year matches")
        );

        let yearStatus = "not_provided";
        if (yearProvided) {
          yearStatus = yearMatch ? "verified" : "mismatch";
        }

        // IEEE Text resolution
        const ieeeText = citation.canonical_citation || citation.corrected_citation;

        return (
          <div
            key={index}
            className="bg-white dark:bg-[#1F1F24] border-[2.5px] border-black rounded-2xl shadow-[6px_6px_0px_#111] p-5 sm:p-6 transition-colors space-y-4"
          >
            {/* Top Bar: Citation Header & Statuses */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b-2 border-black">
              <div className="flex items-center gap-3">
                {/* Number Badge */}
                <div className="w-8 h-8 rounded-xl bg-black text-white font-mono text-sm font-black flex items-center justify-center border-2 border-black shadow-[1.5px_1.5px_0px_#111]">
                  #{index + 1}
                </div>
                <div>
                  <h4 className="font-black text-base sm:text-lg text-neutral-900 dark:text-neutral-100 font-display">
                    {auditStage === "submitted"
                      ? `#${index + 1} Submitted Citation (Initial Audit)`
                      : `#${index + 1} Citation Verification`}
                  </h4>
                  <p className="font-mono text-xs text-neutral-500 dark:text-neutral-400 font-bold">
                    {subtitle}
                  </p>
                </div>
              </div>

              {/* Status Badge */}
              <span className={`px-3 py-1 rounded-xl border-2 font-mono text-xs font-black uppercase tracking-wider shadow-[2px_2px_0px_#111] ${mainBadgeClass}`}>
                {mainBadgeLabel}
              </span>
            </div>

            {/* Closed-loop rectification notice on final card */}
            {auditStage === "final" && hasCorrections && citation.citation_accurate && (
              <div className="p-2.5 bg-[#D1FAE5] dark:bg-[#064e3b]/40 border-2 border-black rounded-xl text-[#065F46] dark:text-emerald-200 font-mono text-xs flex items-center gap-2 shadow-[1.5px_1.5px_0px_#111]">
                <span>✓</span>
                <span>
                  <b>Closed-Loop Rectification:</b> All submitted metadata discrepancies were corrected and independently re-verified.
                </span>
              </div>
            )}

            {/* Extracted Raw Citation Text */}
            {citation.citation && (
              <div className="p-3.5 bg-[#FAF5EC] dark:bg-[#141416] rounded-xl border-2 border-black space-y-1.5 shadow-[2px_2px_0px_#111]">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] font-black uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                    {auditStage === "submitted" ? "ORIGINAL SUBMITTED RAW CITATION STRING" : "RE-VERIFIED CITATION STRING"}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopyRaw(citation.citation, index)}
                    className="px-2.5 py-0.5 bg-[#EBB13E] hover:bg-[#F4B731] text-black border-2 border-black rounded-lg font-mono text-[11px] font-black shadow-[1.5px_1.5px_0px_#111] cursor-pointer flex items-center gap-1 select-none transition-all"
                  >
                    <span>📋</span>
                    <span>{copiedRawIndex === index ? "Copied" : "Copy"}</span>
                  </button>
                </div>
                <p className="font-mono text-xs sm:text-[13px] text-neutral-900 dark:text-neutral-100 leading-relaxed break-words font-medium">
                  {citation.citation}
                </p>
              </div>
            )}

            {/* SEGMENTED RISK METER BAR */}
            <div className="p-3.5 rounded-xl border-2 border-black bg-white dark:bg-[#27272a] shadow-[2px_2px_0px_#111] space-y-2">
              <div className="flex items-center justify-between font-mono">
                <span className="text-xs font-black uppercase tracking-wider text-neutral-800 dark:text-neutral-200">
                  COMPOSITE HALLUCINATION RISK
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-black text-neutral-900 dark:text-neutral-100">
                    {score} / 100
                  </span>
                  <span className={`px-2 py-0.5 rounded-md border text-[10px] font-black uppercase ${
                    score > 50
                      ? "bg-rose-100 text-rose-800 border-rose-500"
                      : score > 20
                      ? "bg-amber-100 text-amber-800 border-amber-500"
                      : "bg-blue-100 text-blue-800 border-blue-500"
                  }`}>
                    {score > 50 ? "High Risk" : score > 20 ? "Moderate" : "Low Risk"}
                  </span>
                </div>
              </div>

              {/* Segmented Color Bar */}
              <div className="relative w-full h-5 bg-neutral-200 dark:bg-neutral-800 border-2 border-black rounded-lg overflow-hidden flex shadow-[1px_1px_0px_#111]">
                <div className="w-[20%] h-full bg-[#2563EB] border-r-2 border-black" />
                <div className="w-[30%] h-full bg-[#EBB13E] border-r-2 border-black" />
                <div className="w-[50%] h-full bg-[#E0453A]" />
                <div
                  className="absolute top-0 bottom-0 w-2 bg-black -ml-1 border-x border-white shadow-md z-10"
                  style={{ left: `${Math.min(Math.max(score, 3), 97)}%` }}
                />
              </div>

              {/* Scale Ticks */}
              <div className="flex justify-between font-mono text-[10px] text-neutral-500 dark:text-neutral-400 font-bold px-0.5">
                <span>0 Low Risk</span>
                <span>20</span>
                <span>50 Moderate</span>
                <span>100 High Risk</span>
              </div>
            </div>

            {/* BIBLIOGRAPHIC FIELD INTEGRITY CHECKS */}
            <div className="space-y-2">
              <span className="font-mono text-xs font-black uppercase tracking-wider text-neutral-700 dark:text-neutral-300 block">
                {auditStage === "submitted"
                  ? "ORIGINAL SUBMITTED FIELD INTEGRITY CHECKS"
                  : "BIBLIOGRAPHIC FIELD INTEGRITY CHECKS"}
              </span>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-xs">
                {/* DOI Pill */}
                <div className={`p-2 rounded-xl border-2 border-black font-black flex items-center justify-between shadow-[2px_2px_0px_#111] ${
                  doiStatus === "verified"
                    ? "bg-[#2563EB] text-white"
                    : doiStatus === "not_provided"
                    ? "bg-[#FAF5EC] dark:bg-[#27272a] text-neutral-700 dark:text-neutral-300"
                    : "bg-[#E0453A] text-white"
                }`}>
                  <span>DOI</span>
                  <span className="text-[11px] uppercase">
                    {doiStatus === "verified" ? "Verified ✓" : doiStatus === "not_provided" ? "Not Provided" : "Mismatch ✕"}
                  </span>
                </div>

                {/* Authors Pill */}
                <div className={`p-2 rounded-xl border-2 border-black font-black flex items-center justify-between shadow-[2px_2px_0px_#111] ${
                  authorStatus === "verified"
                    ? "bg-[#2563EB] text-white"
                    : authorStatus === "not_provided"
                    ? "bg-[#FAF5EC] dark:bg-[#27272a] text-neutral-700 dark:text-neutral-300"
                    : "bg-[#E0453A] text-white"
                }`}>
                  <span>Authors</span>
                  <span className="text-[11px] uppercase">
                    {authorStatus === "verified" ? "Verified ✓" : authorStatus === "not_provided" ? "Not Provided" : "Corrupted ⚠"}
                  </span>
                </div>

                {/* Venue Pill */}
                <div className={`p-2 rounded-xl border-2 border-black font-black flex items-center justify-between shadow-[2px_2px_0px_#111] ${
                  venueStatus === "verified"
                    ? "bg-[#2563EB] text-white"
                    : venueStatus === "not_provided"
                    ? "bg-[#FAF5EC] dark:bg-[#27272a] text-neutral-700 dark:text-neutral-300"
                    : "bg-[#EBB13E] text-black"
                }`}>
                  <span>Venue</span>
                  <span className="text-[11px] uppercase">
                    {venueStatus === "verified" ? "Verified ✓" : venueStatus === "not_provided" ? "Not Provided" : "Inaccurate ⚠"}
                  </span>
                </div>

                {/* Year Pill */}
                <div className={`p-2 rounded-xl border-2 border-black font-black flex items-center justify-between shadow-[2px_2px_0px_#111] ${
                  yearStatus === "verified"
                    ? "bg-[#2563EB] text-white"
                    : yearStatus === "not_provided"
                    ? "bg-[#FAF5EC] dark:bg-[#27272a] text-neutral-700 dark:text-neutral-300"
                    : "bg-[#E0453A] text-white"
                }`}>
                  <span>Year</span>
                  <span className="text-[11px] uppercase">
                    {yearStatus === "verified" ? "Verified ✓" : yearStatus === "not_provided" ? "Not Provided" : "Mismatch ✕"}
                  </span>
                </div>
              </div>
            </div>

            {/* Matched Scholarly Metadata (Authoritative Record) */}
            {citation.matched_title && (
              <div className="p-3.5 bg-[#FAF5EC] dark:bg-[#18181b] rounded-xl border-2 border-black font-mono text-xs shadow-[2px_2px_0px_#111]">
                <span className="font-black text-neutral-800 dark:text-neutral-200 uppercase block mb-1.5">
                  Authoritative Cross-Referenced Record
                </span>
                <div className="space-y-1 text-neutral-800 dark:text-neutral-200">
                  <p><b className="text-neutral-500 uppercase text-[11px]">Title:</b> {citation.matched_title}</p>
                  {citation.matched_authors && citation.matched_authors.length > 0 && (
                    <p><b className="text-neutral-500 uppercase text-[11px]">Authors:</b> {Array.isArray(citation.matched_authors) ? citation.matched_authors.join(", ") : citation.matched_authors}</p>
                  )}
                  {citation.matched_venue && (
                    <p><b className="text-neutral-500 uppercase text-[11px]">Venue:</b> {citation.matched_venue}</p>
                  )}
                  {citation.matched_year && (
                    <p><b className="text-neutral-500 uppercase text-[11px]">Year:</b> {citation.matched_year}</p>
                  )}
                  {citation.matched_doi && (
                    <p><b className="text-neutral-500 uppercase text-[11px]">DOI:</b> <a href={`https://doi.org/${citation.matched_doi}`} target="_blank" rel="noreferrer" className="text-blue-600 underline font-bold">{citation.matched_doi}</a></p>
                  )}
                </div>
              </div>
            )}

            {/* Verification Findings */}
            {citation.reason && citation.reason.length > 0 && (
              <div className="space-y-1.5">
                <span className="font-mono text-xs font-black text-neutral-800 dark:text-neutral-200 uppercase block">
                  VERIFICATION FINDINGS:
                </span>
                <ul className="space-y-1 pl-1">
                  {citation.reason.map((r, i) => (
                    <li key={i} className="font-mono text-xs text-neutral-800 dark:text-neutral-200 flex items-start gap-2">
                      <span className="text-[#EBB13E] font-black text-sm leading-tight">▸</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Claim-to-Source Semantic Support Check */}
            {citation.claim_verification && (
              <div className={`p-3.5 rounded-xl border-2 border-black font-mono text-xs shadow-[2px_2px_0px_#111] ${
                citation.claim_verification.status === "supported"
                  ? "bg-emerald-50 dark:bg-emerald-950/20 text-emerald-900 dark:text-emerald-200"
                  : citation.claim_verification.status === "unsupported_claim"
                  ? "bg-rose-50 dark:bg-rose-950/20 text-rose-900 dark:text-rose-200"
                  : citation.claim_verification.status === "not_found"
                  ? "bg-rose-50 dark:bg-rose-950/20 text-rose-900 dark:text-rose-200"
                  : "bg-amber-50 dark:bg-amber-950/20 text-amber-900 dark:text-amber-200"
              }`}>
                <div className="flex flex-wrap items-center justify-between gap-1 font-black mb-1">
                  <div className="flex items-center gap-1.5">
                    <span>
                      {citation.claim_verification.status === "supported" ? "✓" : citation.claim_verification.status === "unsupported_claim" ? "✕" : "ℹ"}
                    </span>
                    <span className="uppercase tracking-wide">
                      {citation.claim_verification.status === "supported"
                        ? "Claim-to-Source Support: Corroborated"
                        : citation.claim_verification.status === "unsupported_claim"
                        ? "Claim-to-Source Support: Mismatch / Conflict"
                        : citation.claim_verification.status === "not_found"
                        ? "Claim-to-Source Support: Paper Not Found"
                        : "Claim-to-Source Support: Insufficient Evidence"}
                    </span>
                  </div>
                  <span className="text-[10px] uppercase font-bold opacity-80">
                    Evidence: {citation.claim_verification.evidence_type || "Registry Metadata"}
                  </span>
                </div>

                {citation.claim_verification.claim && (
                  <p className="mt-1 mb-1.5 text-[11px] opacity-90">
                    <b className="uppercase">Associated Claim:</b> &ldquo;{citation.claim_verification.claim}&rdquo;
                  </p>
                )}

                {citation.claim_verification.reason && (
                  <p className="leading-relaxed opacity-95">
                    {citation.claim_verification.reason}
                  </p>
                )}

                {citation.claim_verification.evidence && (
                  <div className="mt-2 p-2 bg-white/70 dark:bg-black/30 rounded-lg border border-black/20 text-[11px]">
                    <span className="block font-bold uppercase text-[10px] opacity-75 mb-0.5">Scholarly Evidence Excerpt:</span>
                    <p className="italic leading-relaxed">{citation.claim_verification.evidence}</p>
                  </div>
                )}
              </div>
            )}

            {/* Prompt Consistency Check */}
            {citation.prompt_consistency && citation.prompt_consistency.checked && (
              <div className={`p-3 rounded-xl border-2 border-black font-mono text-xs shadow-[2px_2px_0px_#111] ${
                citation.prompt_consistency.matches
                  ? "bg-emerald-50 dark:bg-emerald-950/20 text-emerald-900 dark:text-emerald-200"
                  : "bg-amber-50 dark:bg-amber-950/20 text-amber-900 dark:text-amber-200"
              }`}>
                <div className="flex items-center gap-2 font-black mb-1">
                  <span>{citation.prompt_consistency.matches ? "✓" : "⚠"}</span>
                  <span>
                    Prompt Consistency: {citation.prompt_consistency.matches ? "Matches Prompt Metadata" : "Prompt Metadata Mismatch"}
                  </span>
                </div>
                <p className="leading-relaxed opacity-90">
                  {citation.prompt_consistency.explanation}
                </p>
              </div>
            )}

            {/* Suggested / Verified IEEE Citation */}
            <div className="pt-2 border-t-2 border-black/10 dark:border-white/10">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="font-mono text-xs font-black text-neutral-900 dark:text-neutral-100 uppercase flex items-center gap-1.5">
                  <span className="text-[#EBB13E] text-sm">✦</span> {citation.citation_accurate ? "Verified Canonical IEEE Citation" : "Suggested IEEE Citation"}
                </span>
                {ieeeText && (
                  <button
                    type="button"
                    onClick={() => handleCopyCitation(ieeeText, index)}
                    className="px-2.5 py-1 bg-[#EBB13E] hover:bg-[#F4B731] text-neutral-900 border-2 border-black rounded-lg font-mono text-[11px] font-black shadow-btn cursor-pointer transition-all select-none"
                  >
                    {copiedIndex === index ? "✓ Copied" : "Copy IEEE"}
                  </button>
                )}
              </div>

              <pre className="bg-[#FAF5EC] dark:bg-[#121214] text-neutral-900 dark:text-neutral-100 p-3.5 rounded-xl border-2 border-black font-mono text-xs leading-relaxed whitespace-pre-wrap break-words shadow-[2px_2px_0px_#111]">
                {ieeeText || (citation.paper_exists === false ? "No reliable correction found (paper could not be verified in scholarly databases)." : "Citation verified accurate against scholarly registry record.")}
              </pre>
            </div>
          </div>
        );
      })}
    </div>
  );
}
