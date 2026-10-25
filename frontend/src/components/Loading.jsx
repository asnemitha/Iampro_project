export default function Loading() {
  return (
    <div className="bg-white dark:bg-[#1f1f26] border-[2.5px] border-black rounded-2xl shadow-card p-8 flex flex-col items-center justify-center min-h-[460px] text-center transition-colors">
      {/* Animated Shield/Radar Icon */}
      <div className="relative mb-6">
        <div className="w-20 h-20 rounded-2xl bg-[#ebb23f] border-2 border-black shadow-[4px_4px_0px_#000] flex items-center justify-center animate-bounce">
          <svg 
            className="w-10 h-10 text-neutral-900" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2.2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          >
            <path d="M12 2L4 5V11.5C4 16.5 7.4 21.1 12 22C16.6 21.1 20 16.5 20 11.5V5L12 2Z" />
            <path d="M12 8v4" />
            <path d="M12 16h.01" />
          </svg>
        </div>
      </div>

      <h2 className="font-black text-2xl text-neutral-900 dark:text-neutral-100 font-display mb-2">
        Verifying Citations...
      </h2>
      
      <p className="font-mono text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 max-w-sm mb-6 leading-relaxed">
        Cross-referencing scholarly records across Crossref, DataCite, Semantic Scholar, and OpenAlex.
      </p>

      {/* Progress Pills */}
      <div className="space-y-2 w-full max-w-xs text-left font-mono text-xs">
        <div className="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
          <span className="w-2 h-2 rounded-full bg-[#16a34a] animate-ping" />
          <span>Security screening & prompt classification</span>
        </div>
        <div className="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
          <span className="w-2 h-2 rounded-full bg-[#f5b731] animate-pulse" />
          <span>Multi-source metadata retrieval</span>
        </div>
        <div className="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
          <span className="w-2 h-2 rounded-full bg-[#2563eb] animate-pulse" />
          <span>RapidFuzz candidate ranking & scoring</span>
        </div>
      </div>
    </div>
  );
}
