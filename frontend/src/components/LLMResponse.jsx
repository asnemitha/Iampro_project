import { useState } from "react";

export default function LLMResponse({ response }) {
  const [copied, setCopied] = useState(false);

  if (!response) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(response);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white dark:bg-[#1f1f26] border-2 border-black rounded-xl shadow-card-sm p-4 sm:p-5 mb-5 transition-colors">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          {/* Terminal / Code Icon */}
          <svg className="w-5 h-5 text-neutral-800 dark:text-neutral-200" fill="none" stroke="currentColor" strokeWidth="2.2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span className="font-mono text-xs font-extrabold uppercase tracking-wider text-neutral-800 dark:text-neutral-200">
            LLM GENERATED RESPONSE
          </span>
        </div>

        <button
          onClick={handleCopy}
          className="px-2.5 py-1 bg-white dark:bg-[#27272a] text-neutral-700 dark:text-neutral-200 hover:text-black dark:hover:text-white border border-black rounded-lg font-mono text-[11px] font-bold shadow-[1.5px_1.5px_0px_#000] cursor-pointer transition-all"
        >
          {copied ? "✓ Copied" : "Copy Output"}
        </button>
      </div>

      <pre className="bg-[#faf4eb] dark:bg-[#121214] text-neutral-900 dark:text-neutral-100 p-4 rounded-xl border border-black font-mono text-xs sm:text-[13px] leading-relaxed whitespace-pre-wrap break-words overflow-x-auto">
        {response}
      </pre>
    </div>
  );
}
