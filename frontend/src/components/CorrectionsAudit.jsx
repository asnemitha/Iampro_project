import { useState } from "react";

export default function CorrectionsAudit({ corrections = [] }) {
  const [copiedIdx, setCopiedIdx] = useState(null);

  if (!corrections || corrections.length === 0) {
    return null;
  }

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="bg-white dark:bg-[#1f1f26] border-2 border-black rounded-xl shadow-card-sm p-4 sm:p-5 mb-5 transition-colors">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b-2 border-black">
        <div className="flex items-center gap-2">
          <span className="w-7 h-7 rounded-lg bg-[#f5b731] border-2 border-black font-mono text-xs font-black flex items-center justify-center text-black shadow-[1.5px_1.5px_0px_#000]">
            ✦
          </span>
          <div>
            <h3 className="font-mono text-xs sm:text-sm font-black uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
              CORRECTIONS APPLIED & RE-VERIFIED ({corrections.length})
            </h3>
            <span className="font-mono text-[11px] text-neutral-500 dark:text-neutral-400 block">
              Automated evidence-based corrections across closed-loop verification iterations
            </span>
          </div>
        </div>

        <span className="px-2.5 py-1 bg-amber-100 dark:bg-amber-950/60 text-amber-900 dark:text-amber-200 border border-black rounded-lg font-mono text-[11px] font-bold shadow-[1px_1px_0px_#000]">
          Closed-Loop Rectification
        </span>
      </div>

      {/* List of Applied Corrections */}
      <div className="space-y-4">
        {corrections.map((corr, idx) => (
          <div
            key={idx}
            className="p-3.5 rounded-xl border border-black bg-[#faf4eb] dark:bg-[#27272a] shadow-[1.5px_1.5px_0px_#000] space-y-3"
          >
            {/* Top row of card */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-mono text-xs font-black uppercase text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-[#f5b731] border border-black text-black flex items-center justify-center text-[10px]">
                  {idx + 1}
                </span>
                Correction #{idx + 1} (Iteration {corr.iteration || 1})
              </span>

              {/* Verified in next step badge */}
              <span
                className={`px-2 py-0.5 rounded-md border border-black font-mono text-[10px] font-bold shadow-[1px_1px_0px_#000] ${
                  corr.verified_in_next_step
                    ? "bg-emerald-100 text-emerald-900 border-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-200"
                    : "bg-amber-100 text-amber-900 border-amber-600 dark:bg-amber-950/60 dark:text-amber-200"
                }`}
              >
                {corr.verified_in_next_step ? "✓ Re-verification Passed" : "⚠ Qualified Annotation"}
              </span>
            </div>

            {/* Explanation / Diagnosis */}
            {corr.explanation && (
              <p className="font-mono text-xs text-neutral-700 dark:text-neutral-300 bg-white dark:bg-[#1f1f26] p-2.5 rounded-lg border border-neutral-300 dark:border-neutral-700 leading-relaxed">
                <b className="text-neutral-900 dark:text-neutral-100">Discrepancy Remediation:</b> {corr.explanation}
              </p>
            )}

            {/* Before vs After Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              {/* Original flawed citation */}
              <div className="p-3 rounded-lg border border-rose-400 bg-rose-50/70 dark:bg-rose-950/20 text-rose-900 dark:text-rose-200">
                <span className="block font-bold uppercase text-[10px] text-rose-700 dark:text-rose-300 mb-1">
                  ✕ Original Problematic Citation
                </span>
                <pre className="whitespace-pre-wrap break-words text-[11px] font-normal leading-relaxed">
                  {corr.original_citation}
                </pre>
              </div>

              {/* Corrected citation */}
              <div className="p-3 rounded-lg border border-emerald-400 bg-emerald-50/70 dark:bg-emerald-950/20 text-emerald-900 dark:text-emerald-200">
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="block font-bold uppercase text-[10px] text-emerald-700 dark:text-emerald-300">
                    ✓ Verified Corrected Replacement
                  </span>
                  <button
                    onClick={() => handleCopy(corr.corrected_citation, idx)}
                    className="px-2 py-0.5 bg-white dark:bg-[#1f1f26] text-black dark:text-white border border-black rounded text-[10px] font-bold shadow-[1px_1px_0px_#000] cursor-pointer hover:bg-neutral-100"
                  >
                    {copiedIdx === idx ? "Copied" : "Copy"}
                  </button>
                </div>
                <pre className="whitespace-pre-wrap break-words text-[11px] font-normal leading-relaxed">
                  {corr.corrected_citation}
                </pre>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
