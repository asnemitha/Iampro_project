export default function PromptAnalysis({ analysis }) {
  if (!analysis) return null;

  const isSuspicious = analysis.label_name === "Suspicious";
  const isMalicious = analysis.label_name === "Malicious" || analysis.label === 2;

  let badgeBg = "bg-emerald-100 text-emerald-900 border-emerald-600";
  let statusText = "Safe / Academic Expected";
  let statusColor = "#16a34a";

  if (isSuspicious) {
    badgeBg = "bg-amber-100 text-amber-900 border-amber-600";
    statusText = "Suspicious / Potential Risk";
    statusColor = "#ea580c";
  } else if (isMalicious) {
    badgeBg = "bg-rose-100 text-rose-900 border-rose-600";
    statusText = "Adversarial / Malicious Instruction";
    statusColor = "#dc2626";
  }

  const confidencePct = typeof analysis.confidence === "number" 
    ? (analysis.confidence * 100).toFixed(2) 
    : "99.00";

  return (
    <div className="bg-white dark:bg-[#1f1f26] border-2 border-black rounded-xl shadow-card-sm p-4 sm:p-5 mb-5 transition-colors">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          {/* Security Icon */}
          <svg className="w-5 h-5 text-neutral-800 dark:text-neutral-200" fill="none" stroke="currentColor" strokeWidth="2.2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <span className="font-mono text-xs font-extrabold uppercase tracking-wider text-neutral-800 dark:text-neutral-200">
            PROMPT SAFETY ANALYSIS
          </span>
        </div>

        {/* Status Chip */}
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg border-2 border-black font-mono text-xs font-black uppercase shadow-[1.5px_1.5px_0px_#000] ${badgeBg}`}>
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: statusColor }} />
          {analysis.label_name || "Analyzed"}
        </span>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2 border-t border-neutral-200 dark:border-neutral-700">
        <div className="font-mono text-xs text-neutral-600 dark:text-neutral-400">
          <span>Classification Status: </span>
          <span className="font-bold text-neutral-900 dark:text-neutral-100">{statusText}</span>
        </div>
        
        <div className="font-mono text-xs text-neutral-600 dark:text-neutral-400 flex items-center gap-2">
          <span>Model Confidence:</span>
          <span className="font-bold font-mono px-2 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 border border-black">
            {confidencePct}%
          </span>
        </div>
      </div>
    </div>
  );
}
