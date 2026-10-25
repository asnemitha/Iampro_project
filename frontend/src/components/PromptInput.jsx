export default function PromptInput({
  prompt,
  setPrompt,
  llmOutput = "",
  setLlmOutput = () => {},
  analyze,
  loading,
  onLoadExample,
  onClear,
}) {
  return (
    <div className="bg-white dark:bg-[#1f1f26] border-[2.5px] border-black rounded-2xl shadow-card p-6 flex flex-col justify-between transition-colors">
      <div>
        {/* Header Row */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            {/* Blue Book Icon */}
            <svg 
              className="w-6 h-6 text-[#2563eb]" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2.3" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
            <h2 className="font-black text-lg sm:text-xl tracking-tight text-neutral-900 dark:text-neutral-100 font-display uppercase">
              INPUT CITATIONS
            </h2>
          </div>

          {/* Load Example Button */}
          <button
            type="button"
            onClick={onLoadExample}
            disabled={loading}
            className="bg-[#f5b731] hover:bg-[#eab308] text-neutral-900 border-2 border-black rounded-xl px-3.5 py-1.5 shadow-btn font-mono text-xs sm:text-sm font-bold flex items-center gap-1.5 cursor-pointer disabled:opacity-60 transition-all"
            title="Load an academic benchmark citation example"
          >
            {/* Sparkle Icon */}
            <svg 
              className="w-4 h-4" 
              viewBox="0 0 24 24" 
              fill="currentColor" 
              stroke="none"
            >
              <path d="M12 2L14.39 8.26L21 9.27L16 14.14L17.45 20.73L12 17.27L6.55 20.73L8 14.14L3 9.27L9.61 8.26L12 2Z" />
            </svg>
            <span>Load Example</span>
          </button>
        </div>

        {/* Horizontal Divider */}
        <div className="w-full h-0.5 bg-black my-4" />

        {/* Section 1: User Prompt */}
        <div className="mb-5">
          <label className="block font-mono text-xs font-extrabold tracking-wider text-neutral-800 dark:text-neutral-200 uppercase mb-2">
            1. USER PROMPT (CONTEXT & INSTRUCTIONS)
          </label>
          <div className="relative">
            <textarea
              rows={4}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Provide the citation for ResNet and YOLO in IEEE format..."
              disabled={loading}
              className="w-full bg-white dark:bg-[#27272a] text-neutral-900 dark:text-neutral-100 border-2 border-black rounded-xl p-3.5 shadow-input font-mono text-xs sm:text-[13px] leading-relaxed placeholder:text-neutral-400 dark:placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-[#f5b731] resize-y transition-all"
            />
          </div>
        </div>

        {/* Section 2: LLM-Generated Output (Optional) */}
        <div className="mb-2">
          <label className="block font-mono text-xs font-extrabold tracking-wider text-neutral-800 dark:text-neutral-200 uppercase mb-0.5">
            2. LLM-GENERATED OUTPUT (OPTIONAL - LEAVE EMPTY TO GENERATE ONE)
          </label>
          <span className="block font-mono text-[11px] text-neutral-500 dark:text-neutral-400 mb-2">
            Application feature, not part of the evaluated pipeline.
          </span>
          <div className="relative">
            <textarea
              rows={4}
              value={llmOutput}
              onChange={(e) => setLlmOutput(e.target.value)}
              placeholder="Optional: Leave empty to prompt the backend model to generate an answer, or paste pre-generated citations here."
              disabled={loading}
              className="w-full bg-white dark:bg-[#27272a] text-neutral-900 dark:text-neutral-100 border-2 border-black rounded-xl p-3.5 shadow-input font-mono text-xs sm:text-[13px] leading-relaxed placeholder:text-neutral-400 dark:placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-[#f5b731] resize-y transition-all"
            />
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-6 flex flex-col sm:flex-row items-center gap-3">
        <button
          type="button"
          onClick={analyze}
          disabled={loading || (!prompt.trim() && !llmOutput.trim())}
          className="w-full sm:flex-1 bg-[#f5b731] hover:bg-[#eab308] text-neutral-900 border-2 border-black rounded-xl py-3 px-5 shadow-btn font-mono text-xs sm:text-sm font-extrabold uppercase tracking-wider flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {loading ? (
            <>
              <svg className="animate-spin w-4 h-4 text-black" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              <span>Verifying Citations...</span>
            </>
          ) : (
            <>
              {/* Shield/Check Icon */}
              <svg className="w-4 h-4 text-black" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span>Verify Citations</span>
            </>
          )}
        </button>

        {(prompt.trim() || llmOutput.trim()) && (
          <button
            type="button"
            onClick={onClear}
            disabled={loading}
            className="w-full sm:w-auto bg-white dark:bg-[#27272a] text-neutral-700 dark:text-neutral-300 hover:text-black dark:hover:text-white border-2 border-black rounded-xl py-3 px-4 shadow-btn font-mono text-xs font-bold uppercase tracking-wider transition-all cursor-pointer"
            title="Clear all inputs"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
