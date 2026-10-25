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
    <div className="bg-white dark:bg-[#1F1F24] border-2 border-black rounded-xl shadow-[4px_4px_0px_#111] p-4 sm:p-5 mb-5 transition-colors">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b-2 border-black">
        <div className="flex items-center gap-2">
          <span className="w-7 h-7 rounded-lg bg-[#EBB13E] border-2 border-black font-mono text-xs font-black flex items-center justify-center text-black shadow-[1.5px_1.5px_0px_#111]">
            ✦
          </span>
          <div>
            <h3 className="font-mono text-xs sm:text-sm font-black uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
              CORRECTIONS APPLIED & RE-VERIFIED ({corrections.length})
            </h3>
            <span className="font-mono text-[11px] text-neutral-500 dark:text-neutral-400 block font-medium">
              Automated evidence-based corrections across closed-loop verification iterations
            </span>
          </div>
        </div>

        <span className="px-3 py-1 bg-[#FEF3C7] text-[#92400E] border-2 border-black rounded-xl font-mono text-[11px] font-black shadow-[2px_2px_0px_#111] uppercase">
          Closed-Loop Rectification
        </span>
      </div>

      {/* List of Applied Corrections */}
      <div className="space-y-4">
        {corrections.map((corr, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl border-2 border-black bg-[#FAF5EC] dark:bg-[#27272a] shadow-[2px_2px_0px_#111] space-y-3"
          >
            {/* Top row of card */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-mono text-xs font-black uppercase text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-[#EBB13E] border-2 border-black text-black flex items-center justify-center text-[10px] font-black">
                  {idx + 1}
                </span>
                Correction #{idx + 1} (Iteration {corr.iteration || 1})
              </span>

              {/* Verified badge */}
              <span
                className={`px-2.5 py-0.5 rounded-lg border-2 border-black font-mono text-[10px] font-black shadow-[1px_1px_0px_#111] uppercase ${
                  corr.verified_in_next_step
                    ? "bg-[#D1FAE5] text-[#065F46]"
                    : "bg-[#FEF3C7] text-[#92400E]"
                }`}
              >
                {corr.verified_in_next_step ? "✓ Re-verification Passed" : "⚠ Qualified Annotation"}
              </span>
            </div>

            {/* Explanation / Diagnosis */}
            {corr.explanation && (
              <p className="font-mono text-xs text-neutral-800 dark:text-neutral-200 bg-white dark:bg-[#1F1F24] p-3 rounded-xl border-2 border-black leading-relaxed shadow-[1.5px_1.5px_0px_#111]">
                <b className="text-neutral-900 dark:text-neutral-100 uppercase text-[11px]">Discrepancy Remediation:</b> {corr.explanation}
              </p>
            )}

            {/* Before vs After Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              {/* Original flawed citation */}
              <div className="p-3 rounded-xl border-2 border-black bg-rose-50 dark:bg-rose-950/20 text-rose-950 dark:text-rose-100 shadow-[2px_2px_0px_#111]">
                <span className="block font-black uppercase text-[10px] text-rose-800 dark:text-rose-300 mb-1">
                  ✕ Original Problematic Citation
                </span>
                <pre className="whitespace-pre-wrap break-words text-[11px] font-normal leading-relaxed">
                  {corr.original_citation}
                </pre>
              </div>

              {/* Corrected citation */}
              <div className="p-3 rounded-xl border-2 border-black bg-emerald-50 dark:bg-emerald-950/20 text-emerald-950 dark:text-emerald-100 shadow-[2px_2px_0px_#111]">
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="block font-black uppercase text-[10px] text-emerald-800 dark:text-emerald-300">
                    ✓ Verified Corrected Replacement
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(corr.corrected_citation, idx)}
                    className="px-2 py-0.5 bg-white dark:bg-[#1F1F24] text-black dark:text-white border-2 border-black rounded-lg text-[10px] font-black shadow-btn cursor-pointer select-none"
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
