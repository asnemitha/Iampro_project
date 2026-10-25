export default function VerificationSummary({ summary }) {
  if (!summary) return null;

  const {
    final_status = "unverified",
    total_citations = 0,
    verified_count = 0,
    corrected_and_verified_count = 0,
    unresolved_count = 0,
    iterations_run = 1,
    limitations = "",
  } = summary;

  // Never show a green success badge if unresolved discrepancies exist
  const getStatusBadge = () => {
    if (final_status === "verified" && unresolved_count === 0) {
      return {
        label: "VERIFIED — ZERO UNRESOLVED DISCREPANCIES",
        icon: "✓",
        badgeClass: "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-900 dark:text-emerald-200 border-emerald-600",
        indicator: "bg-emerald-500",
      };
    }
    if (final_status === "partially_verified") {
      return {
        label: `PARTIALLY VERIFIED — ${unresolved_count} UNRESOLVED CITATION(S)`,
        icon: "⚠",
        badgeClass: "bg-amber-100 dark:bg-amber-950/60 text-amber-900 dark:text-amber-200 border-amber-600",
        indicator: "bg-amber-500",
      };
    }
    if (final_status === "correction_failed") {
      return {
        label: "CORRECTION ATTEMPTS EXHAUSTED — DISCREPANCIES PERSIST",
        icon: "✕",
        badgeClass: "bg-rose-100 dark:bg-rose-950/60 text-rose-900 dark:text-rose-200 border-rose-600",
        indicator: "bg-rose-500",
      };
    }
    return {
      label: "UNVERIFIED — INSUFFICIENT EVIDENCE / REGISTRY OUTAGE",
      icon: "?",
      badgeClass: "bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-200 border-neutral-600",
      indicator: "bg-neutral-500",
    };
  };

  const statusConfig = getStatusBadge();

  return (
    <div className="bg-white dark:bg-[#1f1f26] border-2 border-black rounded-xl shadow-card-sm p-4 sm:p-5 mb-5 transition-colors">
      {/* Top Row: Title & High-Contrast Status Badge */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b-2 border-black">
        <div className="flex items-center gap-2">
          <span className="w-7 h-7 rounded-lg bg-[#f5b731] border-2 border-black font-mono text-xs font-black flex items-center justify-center text-black shadow-[1.5px_1.5px_0px_#000]">
            ⚡
          </span>
          <h3 className="font-mono text-xs sm:text-sm font-black uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
            END-TO-END VERIFICATION STATUS
          </h3>
        </div>

        {/* Status Badge */}
        <div className={`px-3 py-1 rounded-lg border-2 border-black font-mono text-xs font-black uppercase tracking-wider shadow-[1.5px_1.5px_0px_#000] flex items-center gap-1.5 ${statusConfig.badgeClass}`}>
          <span>{statusConfig.icon}</span>
          <span>{statusConfig.label}</span>
        </div>
      </div>

      {/* 4-Metric Statistics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 my-3.5">
        {/* Total Citations Checked */}
        <div className="p-3 rounded-xl border border-black bg-[#faf4eb] dark:bg-[#27272a] shadow-[1.5px_1.5px_0px_#000]">
          <span className="font-mono text-[10px] font-bold text-neutral-500 dark:text-neutral-400 block uppercase">
            Total Checked
          </span>
          <span className="font-mono text-lg font-black text-neutral-900 dark:text-neutral-100 mt-1 block">
            {total_citations}
          </span>
        </div>

        {/* Verified Citations */}
        <div className="p-3 rounded-xl border border-black bg-[#faf4eb] dark:bg-[#27272a] shadow-[1.5px_1.5px_0px_#000]">
          <span className="font-mono text-[10px] font-bold text-neutral-500 dark:text-neutral-400 block uppercase">
            Verified Valid
          </span>
          <span className="font-mono text-lg font-black text-emerald-600 dark:text-emerald-400 mt-1 block">
            {verified_count}
          </span>
        </div>

        {/* Corrected & Subsequently Verified */}
        <div className="p-3 rounded-xl border border-black bg-[#faf4eb] dark:bg-[#27272a] shadow-[1.5px_1.5px_0px_#000]">
          <span className="font-mono text-[10px] font-bold text-neutral-500 dark:text-neutral-400 block uppercase">
            Corrected & Re-verified
          </span>
          <span className="font-mono text-lg font-black text-[#f5b731] mt-1 block">
            {corrected_and_verified_count}
          </span>
        </div>

        {/* Unresolved Discrepancies */}
        <div className={`p-3 rounded-xl border border-black shadow-[1.5px_1.5px_0px_#000] ${
          unresolved_count > 0 
            ? "bg-rose-50 dark:bg-rose-950/40 border-rose-600" 
            : "bg-[#faf4eb] dark:bg-[#27272a]"
        }`}>
          <span className="font-mono text-[10px] font-bold text-neutral-500 dark:text-neutral-400 block uppercase">
            Unresolved Issues
          </span>
          <span className={`font-mono text-lg font-black mt-1 block ${
            unresolved_count > 0 ? "text-rose-600 dark:text-rose-400" : "text-neutral-900 dark:text-neutral-100"
          }`}>
            {unresolved_count}
          </span>
        </div>
      </div>

      {/* Limitations & Provenance Notice */}
      {limitations && (
        <div className="p-3 bg-neutral-50 dark:bg-[#18181b] rounded-lg border border-neutral-300 dark:border-neutral-700 font-mono text-xs">
          <div className="flex items-center gap-1.5 font-bold text-neutral-700 dark:text-neutral-300 uppercase mb-1">
            <span>ℹ</span>
            <span>Verification Limitations & Academic Scope ({iterations_run} iteration{iterations_run > 1 ? "s" : ""} executed):</span>
          </div>
          <p className="text-neutral-600 dark:text-neutral-400 leading-relaxed">
            {limitations}
          </p>
        </div>
      )}
    </div>
  );
}
