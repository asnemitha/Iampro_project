import { useState } from "react";

export default function ResponseTabs({
  finalResponse = "",
  originalResponse = "",
  hasCorrections = false,
  unresolvedCount = 0,
}) {
  const [activeTab, setActiveTab] = useState("final");
  const [copied, setCopied] = useState(false);

  const displayResponse = activeTab === "original" ? originalResponse : finalResponse;

  const handleCopy = () => {
    navigator.clipboard.writeText(displayResponse);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!finalResponse && !originalResponse) return null;

  return (
    <div className="bg-white dark:bg-[#1f1f26] border-2 border-black rounded-xl shadow-card-sm p-4 sm:p-5 mb-5 transition-colors">
      {/* Top Controls: Tabs & Copy */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3 pb-3 border-b-2 border-black">
        <div className="flex flex-wrap items-center gap-2">
          {/* Tab 1: Final Verified Response */}
          <button
            type="button"
            onClick={() => setActiveTab("final")}
            className={`px-3 py-1.5 rounded-lg border-2 border-black font-mono text-xs font-black uppercase tracking-wider shadow-btn cursor-pointer transition-all flex items-center gap-1.5 ${
              activeTab === "final"
                ? "bg-[#f5b731] text-black shadow-[2.5px_2.5px_0px_#000]"
                : "bg-white dark:bg-[#27272a] text-neutral-700 dark:text-neutral-300 hover:text-black dark:hover:text-white"
            }`}
          >
            <span>✓</span>
            <span>Final Re-verified Response</span>
          </button>

          {/* Tab 2: Original LLM Response (if different or available) */}
          {originalResponse && originalResponse !== finalResponse && (
            <button
              type="button"
              onClick={() => setActiveTab("original")}
              className={`px-3 py-1.5 rounded-lg border-2 border-black font-mono text-xs font-black uppercase tracking-wider shadow-btn cursor-pointer transition-all flex items-center gap-1.5 ${
                activeTab === "original"
                  ? "bg-[#f5b731] text-black shadow-[2.5px_2.5px_0px_#000]"
                  : "bg-white dark:bg-[#27272a] text-neutral-700 dark:text-neutral-300 hover:text-black dark:hover:text-white"
              }`}
            >
              <span>⏮</span>
              <span>Original LLM Output</span>
            </button>
          )}

          {/* Tab 3: Side-by-Side Comparison (if corrections were made) */}
          {hasCorrections && originalResponse && originalResponse !== finalResponse && (
            <button
              type="button"
              onClick={() => setActiveTab("compare")}
              className={`px-3 py-1.5 rounded-lg border-2 border-black font-mono text-xs font-black uppercase tracking-wider shadow-btn cursor-pointer transition-all flex items-center gap-1.5 ${
                activeTab === "compare"
                  ? "bg-[#f5b731] text-black shadow-[2.5px_2.5px_0px_#000]"
                  : "bg-white dark:bg-[#27272a] text-neutral-700 dark:text-neutral-300 hover:text-black dark:hover:text-white"
              }`}
            >
              <span>⚖</span>
              <span>Comparison View</span>
            </button>
          )}
        </div>

        {/* Copy Button */}
        {activeTab !== "compare" && (
          <button
            type="button"
            onClick={handleCopy}
            className="px-3 py-1 bg-white dark:bg-[#27272a] text-neutral-800 dark:text-neutral-200 hover:text-black dark:hover:text-white border-2 border-black rounded-lg font-mono text-xs font-bold shadow-[2px_2px_0px_#000] cursor-pointer transition-all"
          >
            {copied ? "✓ Copied" : "Copy Output"}
          </button>
        )}
      </div>

      {/* Unresolved / Qualified Warning Banner if applicable */}
      {unresolvedCount > 0 && activeTab === "final" && (
        <div className="mb-3 p-2.5 rounded-lg border border-amber-500 bg-amber-50 dark:bg-amber-950/30 text-amber-900 dark:text-amber-200 font-mono text-xs flex items-center gap-2">
          <span>⚠</span>
          <span>
            <b>Notice:</b> This response contains {unresolvedCount} citation(s) that could not be verified in scholarly databases. Transparent qualifications have been retained in the text.
          </span>
        </div>
      )}

      {/* Main Single-Tab View */}
      {activeTab !== "compare" && (
        <pre className="bg-[#faf4eb] dark:bg-[#121214] text-neutral-900 dark:text-neutral-100 p-4 rounded-xl border border-black font-mono text-xs sm:text-[13px] leading-relaxed whitespace-pre-wrap break-words overflow-x-auto shadow-inner">
          {displayResponse}
        </pre>
      )}

      {/* Side-by-Side Comparison View */}
      {activeTab === "compare" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
          {/* Left: Original */}
          <div className="space-y-1.5">
            <span className="font-mono text-xs font-black uppercase text-rose-700 dark:text-rose-400 block flex items-center gap-1">
              <span>✕</span>
              <span>Original Baseline (With Discrepancies)</span>
            </span>
            <pre className="bg-rose-50/50 dark:bg-rose-950/20 text-neutral-900 dark:text-neutral-100 p-3.5 rounded-xl border border-rose-300 dark:border-rose-900 font-mono text-xs leading-relaxed whitespace-pre-wrap break-words h-80 overflow-y-auto">
              {originalResponse}
            </pre>
          </div>

          {/* Right: Final Verified */}
          <div className="space-y-1.5">
            <span className="font-mono text-xs font-black uppercase text-emerald-700 dark:text-emerald-400 block flex items-center gap-1">
              <span>✓</span>
              <span>Final Verified & Corrected Output</span>
            </span>
            <pre className="bg-emerald-50/50 dark:bg-emerald-950/20 text-neutral-900 dark:text-neutral-100 p-3.5 rounded-xl border border-emerald-300 dark:border-emerald-900 font-mono text-xs leading-relaxed whitespace-pre-wrap break-words h-80 overflow-y-auto">
              {finalResponse}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
