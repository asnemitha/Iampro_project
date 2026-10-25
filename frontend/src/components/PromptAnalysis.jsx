export default function PromptAnalysis({ analysis }) {
  if (!analysis) return null;

  const isSuspicious = analysis.label_name === "Suspicious";
  const isMalicious = analysis.label_name === "Malicious" || analysis.label === 2;

  let badgeBg = "bg-[#D1FAE5] text-[#065F46] border-black";
  let statusText = "Safe / Academic Expected";
  let statusColor = "#16A34A";

  if (isSuspicious) {
    badgeBg = "bg-[#FEF3C7] text-[#92400E] border-black";
    statusText = "Suspicious / Potential Risk";
    statusColor = "#EA580C";
  } else if (isMalicious) {
    badgeBg = "bg-[#FFE4E6] text-[#9F1239] border-black";
    statusText = "Adversarial / Malicious Instruction";
    statusColor = "#DC2626";
  }

  const confidencePct = typeof analysis.confidence === "number"
    ? (analysis.confidence * 100).toFixed(1)
    : "99.0";

  return (
    <div className="bg-white dark:bg-[#1F1F24] border-2 border-black rounded-xl shadow-[4px_4px_0px_#111] p-4 sm:p-5 transition-colors">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          {/* Security Icon */}
          <svg className="w-5 h-5 text-neutral-800 dark:text-neutral-200" fill="none" stroke="currentColor" strokeWidth="2.2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <span className="font-mono text-xs font-black uppercase tracking-wider text-neutral-800 dark:text-neutral-200">
            PROMPT SAFETY ANALYSIS
          </span>
        </div>

        {/* Status Chip */}
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl border-2 font-mono text-xs font-black uppercase shadow-[2px_2px_0px_#111] ${badgeBg}`}>
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: statusColor }} />
          {analysis.label_name || "Safe"}
        </span>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2.5 border-t-2 border-black/10 dark:border-white/10">
        <div className="font-mono text-xs text-neutral-600 dark:text-neutral-400">
          <span>Classification Status: </span>
          <span className="font-bold text-neutral-900 dark:text-neutral-100">{statusText}</span>
        </div>
        
        <div className="font-mono text-xs text-neutral-600 dark:text-neutral-400 flex items-center gap-2">
          <span>Model Confidence:</span>
          <span className="font-black font-mono px-2.5 py-0.5 rounded-lg bg-[#FAF5EC] dark:bg-[#27272a] text-neutral-900 dark:text-neutral-100 border-2 border-black shadow-[1.5px_1.5px_0px_#111]">
            {confidencePct}%
          </span>
        </div>
      </div>
    </div>
  );
}
