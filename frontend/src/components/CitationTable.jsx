import { useState } from "react";

export default function CitationTable({ citations }) {
  const [copiedIndex, setCopiedIndex] = useState(null);

  if (!citations || citations.length === 0) {
    return (
      <div className="bg-white dark:bg-[#1f1f26] border-2 border-black rounded-xl shadow-card-sm p-6 text-center">
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

  function getScoreBadge(score) {
    if (score === null || score === undefined || typeof score !== "number") {
      return {
        label: "N/A",
        bg: "bg-neutral-100 text-neutral-800 border-neutral-400",
        indicator: "bg-neutral-400"
      };
    }
    if (score <= 20) {
      return {
        label: score,
        bg: "bg-emerald-100 text-emerald-900 border-emerald-500",
        indicator: "bg-emerald-500",
        textClass: "good"
      };
    }
    if (score <= 50) {
      return {
        label: score,
        bg: "bg-amber-100 text-amber-900 border-amber-500",
        indicator: "bg-amber-500",
        textClass: "medium"
      };
    }
    return {
      label: score,
      bg: "bg-rose-100 text-rose-900 border-rose-500",
      indicator: "bg-rose-500",
      textClass: "bad"
    };
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Citation Table Icon */}
          <svg className="w-5 h-5 text-neutral-800 dark:text-neutral-200" fill="none" stroke="currentColor" strokeWidth="2.2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="font-mono text-sm font-black uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
            DETAILED CITATION VERIFICATION RESULTS ({citations.length})
          </h3>
        </div>
      </div>

      {citations.map((citation, index) => {
        const scoreInfo = getScoreBadge(citation.hallucination_score);
        const existsStatus = citation.paper_exists === true ? "Verified Exists" : citation.paper_exists === false ? "Paper Not Found" : "Unverified";
        const existsBg = citation.paper_exists === true 
          ? "bg-emerald-100 text-emerald-800 border-emerald-600" 
          : citation.paper_exists === false 
            ? "bg-rose-100 text-rose-800 border-rose-600" 
            : "bg-amber-100 text-amber-800 border-amber-600";

        return (
          <div
            key={index}
            className="bg-white dark:bg-[#1f1f26] border-2 border-black rounded-xl shadow-card-sm p-5 transition-colors"
          >
            {/* Top Bar: Citation Header & Statuses */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b-2 border-black">
              <div className="flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-lg bg-[#f5b731] border-2 border-black font-mono text-xs font-black flex items-center justify-center text-black shadow-[1.5px_1.5px_0px_#000]">
                  #{index + 1}
                </span>
                <span className="font-black text-base text-neutral-900 dark:text-neutral-100 font-display">
                  Citation {index + 1}
                </span>
              </div>

              {/* Status Chips */}
              <div className="flex flex-wrap items-center gap-2">
                <span className={`px-2.5 py-1 rounded-md border border-black font-mono text-[11px] font-bold shadow-[1px_1px_0px_#000] ${existsBg}`}>
                  {existsStatus}
                </span>

                {citation.hallucination_type && (
                  <span className="px-2.5 py-1 rounded-md border border-black bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 font-mono text-[11px] font-bold shadow-[1px_1px_0px_#000]">
                    {citation.hallucination_type}
                  </span>
                )}
              </div>
            </div>

            {/* Extracted Raw Citation Text */}
            {citation.citation && (
              <div className="my-3 p-3 bg-[#faf4eb] dark:bg-[#121214] rounded-lg border border-black">
                <span className="font-mono text-[10px] font-extrabold uppercase tracking-wider text-neutral-500 block mb-1">
                  Extracted Reference Text
                </span>
                <p className="font-mono text-xs text-neutral-800 dark:text-neutral-200 leading-relaxed break-words">
                  {citation.citation}
                </p>
              </div>
            )}

            {/* Metric Score Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 my-3.5">
              {/* Hallucination Score */}
              <div className="p-2.5 rounded-lg border border-black bg-white dark:bg-[#27272a] shadow-[1.5px_1.5px_0px_#000]">
                <span className="font-mono text-[10px] font-bold text-neutral-500 dark:text-neutral-400 block uppercase">
                  Hallucination Score
                </span>
                <div className="flex items-center gap-1.5 mt-1">
                  <span className={`w-2.5 h-2.5 rounded-full ${scoreInfo.indicator}`} />
                  <span className="font-mono text-base font-black text-neutral-900 dark:text-neutral-100">
                    {scoreInfo.label}
                  </span>
                  <span className="font-mono text-[10px] text-neutral-400">/100</span>
                </div>
              </div>

              {/* Confidence */}
              <div className="p-2.5 rounded-lg border border-black bg-white dark:bg-[#27272a] shadow-[1.5px_1.5px_0px_#000]">
                <span className="font-mono text-[10px] font-bold text-neutral-500 dark:text-neutral-400 block uppercase">
                  Confidence
                </span>
                <span className="font-mono text-sm font-extrabold text-neutral-900 dark:text-neutral-100 mt-1 block">
                  {citation.confidence || "Evaluated"}
                </span>
              </div>

              {/* Title Match */}
              <div className="p-2.5 rounded-lg border border-black bg-white dark:bg-[#27272a] shadow-[1.5px_1.5px_0px_#000]">
                <span className="font-mono text-[10px] font-bold text-neutral-500 dark:text-neutral-400 block uppercase">
                  Title Similarity
                </span>
                <span className="font-mono text-sm font-extrabold text-neutral-900 dark:text-neutral-100 mt-1 block">
                  {citation.title_similarity !== undefined && citation.title_similarity !== null
                    ? `${citation.title_similarity}%`
                    : "—"}
                </span>
              </div>

              {/* DOI Match */}
              <div className="p-2.5 rounded-lg border border-black bg-white dark:bg-[#27272a] shadow-[1.5px_1.5px_0px_#000]">
                <span className="font-mono text-[10px] font-bold text-neutral-500 dark:text-neutral-400 block uppercase">
                  DOI Verification
                </span>
                <span className={`font-mono text-sm font-extrabold mt-1 block ${
                  citation.doi_match === true ? "text-emerald-600" : citation.doi_match === false ? "text-rose-600" : "text-neutral-500"
                }`}>
                  {citation.doi_match === true ? "Verified Match" : citation.doi_match === false ? "Mismatch / Unresolved" : "No DOI"}
                </span>
              </div>
            </div>

            {/* Matched Scholarly Metadata (if found) */}
            {citation.matched_title && (
              <div className="p-3 bg-neutral-50 dark:bg-[#18181b] rounded-lg border border-neutral-300 dark:border-neutral-700 my-3 font-mono text-xs">
                <span className="font-bold text-neutral-700 dark:text-neutral-300 uppercase block mb-1">
                  Authoritative Cross-Referenced Record
                </span>
                <div className="space-y-1 text-neutral-800 dark:text-neutral-200">
                  <p><b className="text-neutral-500">Title:</b> {citation.matched_title}</p>
                  {citation.matched_authors && citation.matched_authors.length > 0 && (
                    <p><b className="text-neutral-500">Authors:</b> {Array.isArray(citation.matched_authors) ? citation.matched_authors.join(", ") : citation.matched_authors}</p>
                  )}
                  {citation.matched_venue && (
                    <p><b className="text-neutral-500">Venue:</b> {citation.matched_venue}</p>
                  )}
                  {citation.matched_year && (
                    <p><b className="text-neutral-500">Year:</b> {citation.matched_year}</p>
                  )}
                  {citation.matched_doi && (
                    <p><b className="text-neutral-500">DOI:</b> <a href={`https://doi.org/${citation.matched_doi}`} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">{citation.matched_doi}</a></p>
                  )}
                </div>
              </div>
            )}

            {/* Claim-to-Source Semantic Support Check */}
            {citation.claim_verification && (
              <div className={`my-3 p-3 rounded-lg border-2 border-black font-mono text-xs shadow-[1.5px_1.5px_0px_#000] ${
                citation.claim_verification.status === "supported"
                  ? "bg-emerald-50 dark:bg-emerald-950/20 text-emerald-900 dark:text-emerald-200"
                  : citation.claim_verification.status === "unsupported_claim"
                  ? "bg-rose-50 dark:bg-rose-950/20 text-rose-900 dark:text-rose-200"
                  : citation.claim_verification.status === "not_found"
                  ? "bg-rose-50 dark:bg-rose-950/20 text-rose-900 dark:text-rose-200"
                  : "bg-amber-50 dark:bg-amber-950/20 text-amber-900 dark:text-amber-200"
              }`}>
                <div className="flex flex-wrap items-center justify-between gap-1 font-bold mb-1">
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
                  <div className="mt-2 p-2 bg-white/70 dark:bg-black/30 rounded border border-black/20 text-[11px]">
                    <span className="block font-bold uppercase text-[10px] opacity-75 mb-0.5">Scholarly Evidence Excerpt:</span>
                    <p className="italic leading-relaxed">{citation.claim_verification.evidence}</p>
                  </div>
                )}
              </div>
            )}

            {/* Verification Reasons & Findings */}
            {citation.reason && citation.reason.length > 0 && (
              <div className="my-3">
                <span className="font-mono text-xs font-bold text-neutral-700 dark:text-neutral-300 uppercase block mb-1.5">
                  Pipeline Diagnostic Findings:
                </span>
                <ul className="space-y-1 pl-2">
                  {citation.reason.map((r, i) => (
                    <li key={i} className="font-mono text-xs text-neutral-700 dark:text-neutral-300 flex items-start gap-2">
                      <span className="text-[#f5b731] font-bold">▸</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Metadata Errors (if any) */}
            {citation.metadata_errors && citation.metadata_errors.length > 0 && (
              <div className="my-3 p-2.5 rounded-lg border border-rose-300 bg-rose-50 dark:bg-rose-950/20 text-rose-800 dark:text-rose-300 font-mono text-xs">
                <span className="font-bold block mb-1">Detected Discrepancies:</span>
                <ul className="list-disc list-inside space-y-0.5">
                  {citation.metadata_errors.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Prompt Consistency Check */}
            {citation.prompt_consistency && citation.prompt_consistency.checked && (
              <div className={`my-3 p-3 rounded-lg border-2 border-black font-mono text-xs shadow-[1.5px_1.5px_0px_#000] ${
                citation.prompt_consistency.matches
                  ? "bg-emerald-50 dark:bg-emerald-950/20 text-emerald-900 dark:text-emerald-200"
                  : "bg-amber-50 dark:bg-amber-950/20 text-amber-900 dark:text-amber-200"
              }`}>
                <div className="flex items-center gap-2 font-bold mb-1">
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

            {/* Suggested IEEE Citation */}
            <div className="mt-4 pt-3 border-t border-neutral-200 dark:border-neutral-700">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="font-mono text-xs font-bold text-neutral-800 dark:text-neutral-200 uppercase flex items-center gap-1.5">
                  <span className="text-amber-500 font-black">✦</span> Suggested IEEE Citation
                </span>
                {citation.corrected_citation && (
                  <button
                    onClick={() => handleCopyCitation(citation.corrected_citation, index)}
                    className="px-2.5 py-1 bg-[#f5b731] hover:bg-[#eab308] text-neutral-900 border border-black rounded-lg font-mono text-[11px] font-bold shadow-[1.5px_1.5px_0px_#000] cursor-pointer transition-all"
                  >
                    {copiedIndex === index ? "✓ Copied" : "Copy IEEE"}
                  </button>
                )}
              </div>

              <pre className="bg-[#fbf7ee] dark:bg-[#121214] text-neutral-900 dark:text-neutral-100 p-3 rounded-xl border border-black font-mono text-xs leading-relaxed whitespace-pre-wrap break-words">
                {citation.corrected_citation || "No reliable correction found."}
              </pre>
            </div>
          </div>
        );
      })}
    </div>
  );
}
