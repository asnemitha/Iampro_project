export default function VerificationSummary({ summary, citations = [] }) {
  if (!summary) return null;

  const {
    final_status = "unverified",
    total_citations = citations.length || 0,
    verified_count = 0,
    unresolved_count = 0,
    limitations = "",
  } = summary;

  // Compute exact category breakdown for the 4 stat tiles based on the final re-verified citations
  let computedVerified = verified_count;
  let computedReview = 0;
  let computedHallucinated = 0;
  let computedAvgRisk = 0;

  if (citations && citations.length > 0) {
    computedVerified = citations.filter(
      (c) => c.paper_exists === true && c.citation_accurate === true && c.claim_verification?.status !== "unsupported_claim"
    ).length;

    computedReview = citations.filter(
      (c) =>
        (c.paper_exists === true && !c.citation_accurate) ||
        c.claim_verification?.status === "unsupported_claim" ||
        (c.metadata_errors && c.metadata_errors.length > 0 && c.paper_exists === true && !c.citation_accurate)
    ).length;

    computedHallucinated = citations.filter(
      (c) => c.paper_exists === false || (typeof c.hallucination_score === "number" && c.hallucination_score > 50)
    ).length;

    const totalScores = citations.reduce((acc, c) => acc + (typeof c.hallucination_score === "number" ? c.hallucination_score : 0), 0);
    computedAvgRisk = Math.round(totalScores / citations.length);
  }

  // Never show a green success badge if unresolved discrepancies exist
  const getStatusBadge = () => {
    if (final_status === "verified" && unresolved_count === 0) {
      return {
        label: "VERIFIED — ZERO UNRESOLVED DISCREPANCIES",
        icon: "✓",
        badgeClass: "bg-[#D1FAE5] text-[#065F46] border-black",
      };
    }
    if (final_status === "partially_verified") {
      return {
        label: `PARTIALLY VERIFIED — ${unresolved_count} UNRESOLVED CITATION(S)`,
        icon: "⚠",
        badgeClass: "bg-[#FEF3C7] text-[#92400E] border-black",
      };
    }
    if (final_status === "correction_failed") {
      return {
        label: "CORRECTION ATTEMPTS EXHAUSTED — DISCREPANCIES PERSIST",
        icon: "✕",
        badgeClass: "bg-[#FFE4E6] text-[#9F1239] border-black",
      };
    }
    return {
      label: "UNVERIFIED — INSUFFICIENT EVIDENCE / REGISTRY OUTAGE",
      icon: "?",
      badgeClass: "bg-neutral-100 text-neutral-900 border-black",
    };
  };

  const statusConfig = getStatusBadge();

  return (
    <div className="space-y-4">
      {/* 4 Stat Summary Cards in a row (Matching Screenshot 1 & 2) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {/* 1. VERIFIED (Royal Blue) */}
        <div className="p-4 rounded-2xl border-[2.5px] border-black bg-[#2563EB] text-white shadow-[4px_4px_0px_#111] flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[11px] font-black uppercase tracking-wider">
              VERIFIED
            </span>
            <svg className="w-5 h-5 text-white stroke-[2.4]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="my-2">
            <span className="font-mono text-3xl sm:text-4xl font-black">
              {computedVerified}
            </span>
          </div>
          <span className="font-mono text-[11px] opacity-90 font-medium">
            Accurate citations
          </span>
        </div>

        {/* 2. NEEDS REVIEW (Mustard Yellow) */}
        <div className="p-4 rounded-2xl border-[2.5px] border-black bg-[#EBB13E] text-black shadow-[4px_4px_0px_#111] flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[11px] font-black uppercase tracking-wider">
              NEEDS REVIEW
            </span>
            <svg className="w-5 h-5 text-black stroke-[2.4]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div className="my-2">
            <span className="font-mono text-3xl sm:text-4xl font-black">
              {computedReview}
            </span>
          </div>
          <span className="font-mono text-[11px] opacity-90 font-medium">
            Corrupted metadata
          </span>
        </div>

        {/* 3. HALLUCINATED (Coral Red) */}
        <div className="p-4 rounded-2xl border-[2.5px] border-black bg-[#E0453A] text-white shadow-[4px_4px_0px_#111] flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[11px] font-black uppercase tracking-wider">
              HALLUCINATED
            </span>
            <svg className="w-5 h-5 text-white stroke-[2.4]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="my-2">
            <span className="font-mono text-3xl sm:text-4xl font-black">
              {computedHallucinated}
            </span>
          </div>
          <span className="font-mono text-[11px] opacity-90 font-medium">
            High risk of ghost paper
          </span>
        </div>

        {/* 4. AVERAGE RISK (White/Neutral) */}
        <div className="p-4 rounded-2xl border-[2.5px] border-black bg-white dark:bg-[#27272a] text-neutral-900 dark:text-neutral-100 shadow-[4px_4px_0px_#111] flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[11px] font-black uppercase tracking-wider">
              AVERAGE RISK
            </span>
            <svg className="w-5 h-5 text-neutral-800 dark:text-neutral-200 stroke-[2.4]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div className="my-2">
            <span className="font-mono text-3xl sm:text-4xl font-black">
              {computedAvgRisk}%
            </span>
          </div>
          <span className="font-mono text-[11px] text-neutral-500 dark:text-neutral-400 font-medium">
            Composite index
          </span>
        </div>
      </div>

      {/* End-to-End Status Banner */}
      <div className="bg-white dark:bg-[#1F1F24] border-2 border-black rounded-xl shadow-[3px_3px_0px_#111] p-3.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-lg bg-[#EBB13E] border border-black font-mono text-xs font-black flex items-center justify-center text-black shadow-[1px_1px_0px_#111]">
            ⚡
          </span>
          <span className="font-mono text-xs font-black uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
            AUDIT STATUS ({total_citations} CITATION{total_citations === 1 ? "" : "S"}):
          </span>
        </div>

        <div className={`px-3 py-1 rounded-xl border-2 font-mono text-xs font-black uppercase tracking-wider shadow-[2px_2px_0px_#111] flex items-center gap-1.5 ${statusConfig.badgeClass}`}>
          <span>{statusConfig.icon}</span>
          <span>{statusConfig.label}</span>
        </div>
      </div>

      {/* Limitations notice */}
      {limitations && (
        <div className="p-3 bg-[#FAF5EC] dark:bg-[#18181b] rounded-xl border-2 border-black font-mono text-xs shadow-[2px_2px_0px_#111]">
          <div className="flex items-center gap-1.5 font-black text-neutral-800 dark:text-neutral-200 uppercase mb-1">
            <span>ℹ</span>
            <span>Verification Limitations & Academic Scope:</span>
          </div>
          <p className="text-neutral-600 dark:text-neutral-400 leading-relaxed">
            {limitations}
          </p>
        </div>
      )}
    </div>
  );
}
