export default function HowItWorksView() {
  const steps = [
    {
      num: "01",
      title: "Prompt Classification & Security Filtering",
      badge: "Security Layer",
      desc: "Analyzes the user's input prompt using fine-tuned classifiers to detect adversarial manipulation, system prompt extraction, or prompt injection. Legitimate academic requests proceed downstream.",
      badgeColor: "bg-[#D1FAE5] text-[#065F46] border-black",
      accentBar: "bg-emerald-500",
      badgeGradient: "from-emerald-400 to-emerald-600 text-white",
      cardBg: "from-white via-white to-emerald-50/40 dark:from-[#1e1e26] dark:via-[#1e1e26] dark:to-emerald-950/20",
      hoverGlow: "hover:ring-2 hover:ring-emerald-500/80 hover:shadow-[7px_7px_0px_#111]",
      shadowStyle: "shadow-[5px_5px_0px_#111]",
    },
    {
      num: "02",
      title: "Citation Extraction & Entity Parsing",
      badge: "NLP Parsing",
      desc: "Discovers references in freeform or numbered text, parsing titles, author lists, publication years, conference/journal venues, and DOI identifiers.",
      badgeColor: "bg-[#DBEAFE] text-[#1E40AF] border-black",
      accentBar: "bg-blue-500",
      badgeGradient: "from-blue-400 to-blue-600 text-white",
      cardBg: "from-white via-white to-blue-50/40 dark:from-[#1e1e26] dark:via-[#1e1e26] dark:to-blue-950/20",
      hoverGlow: "hover:ring-2 hover:ring-blue-500/80 hover:shadow-[7px_7px_0px_#111]",
      shadowStyle: "shadow-[5px_5px_0px_#111]",
    },
    {
      num: "03",
      title: "Authoritative DOI Verification",
      badge: "DOI-First Resolution",
      desc: "Resolves embedded DOIs directly against Crossref and DataCite registries to establish whether the identifier exists and retrieves its ground-truth metadata record.",
      badgeColor: "bg-[#FEF3C7] text-[#92400E] border-black",
      accentBar: "bg-amber-500",
      badgeGradient: "from-amber-300 to-amber-500 text-black",
      cardBg: "from-white via-white to-amber-50/40 dark:from-[#1e1e26] dark:via-[#1e1e26] dark:to-amber-950/20",
      hoverGlow: "hover:ring-2 hover:ring-amber-500/80 hover:shadow-[7px_7px_0px_#111]",
      shadowStyle: "shadow-[5px_5px_0px_#111]",
    },
    {
      num: "04",
      title: "Multi-Source Scholarly Retrieval",
      badge: "Scholarly DBs",
      desc: "Federated queries across Crossref, Semantic Scholar, and OpenAlex aggregate publication candidates even when the DOI is missing or hallucinated.",
      badgeColor: "bg-purple-100 text-purple-900 border-black",
      accentBar: "bg-purple-500",
      badgeGradient: "from-purple-400 to-purple-600 text-white",
      cardBg: "from-white via-white to-purple-50/40 dark:from-[#1e1e26] dark:via-[#1e1e26] dark:to-purple-950/20",
      hoverGlow: "hover:ring-2 hover:ring-purple-500/80 hover:shadow-[7px_7px_0px_#111]",
      shadowStyle: "shadow-[5px_5px_0px_#111]",
    },
    {
      num: "05",
      title: "Candidate Ranking & String Matching",
      badge: "RapidFuzz & Jaro-Winkler",
      desc: "Ranks candidate records using weighted title similarity, author-order invariant matching, year tolerance, and publication venue alias normalization.",
      badgeColor: "bg-[#FFE4E6] text-[#9F1239] border-black",
      accentBar: "bg-rose-500",
      badgeGradient: "from-rose-400 to-rose-600 text-white",
      cardBg: "from-white via-white to-rose-50/40 dark:from-[#1e1e26] dark:via-[#1e1e26] dark:to-rose-950/20",
      hoverGlow: "hover:ring-2 hover:ring-rose-500/80 hover:shadow-[7px_7px_0px_#111]",
      shadowStyle: "shadow-[5px_5px_0px_#111]",
    },
    {
      num: "06",
      title: "Hallucination Scoring (0–100)",
      badge: "Scoring Engine",
      desc: "Assigns a calibrated hallucination score from 0 (verified authentic) to 100 (fabricated). Discrepancies are categorized into 5 specific alteration classes.",
      badgeColor: "bg-[#EBB13E] text-black border-black",
      accentBar: "bg-[#EBB13E]",
      badgeGradient: "from-[#fcd34d] to-[#EBB13E] text-black",
      cardBg: "from-white via-white to-amber-100/50 dark:from-[#1e1e26] dark:via-[#1e1e26] dark:to-amber-950/30",
      hoverGlow: "hover:ring-2 hover:ring-[#EBB13E] hover:shadow-[7px_7px_0px_#111]",
      shadowStyle: "shadow-[5px_5px_0px_#111]",
    },
    {
      num: "07",
      title: "Canonical IEEE Citation Correction",
      badge: "Auto-Correction",
      desc: "When a real paper is identified but citations contain inaccuracies (e.g. altered authors or mistaken year), formats a clean, standardized IEEE citation.",
      badgeColor: "bg-cyan-100 text-cyan-900 border-black",
      accentBar: "bg-cyan-500",
      badgeGradient: "from-cyan-300 to-cyan-500 text-black",
      cardBg: "from-white via-white to-cyan-50/40 dark:from-[#1e1e26] dark:via-[#1e1e26] dark:to-cyan-950/20",
      hoverGlow: "hover:ring-2 hover:ring-cyan-500/80 hover:shadow-[7px_7px_0px_#111]",
      shadowStyle: "shadow-[5px_5px_0px_#111]",
    }
  ];

  const sources = [
    { name: "Crossref", role: "Primary authoritative DOI registry and publisher bibliographic index.", status: "Active" },
    { name: "DataCite", role: "Specialized DOI index for scientific datasets, preprints, and open science.", status: "Active" },
    { name: "Semantic Scholar", role: "Allen Institute AI-indexed corpus of 200M+ research papers and author profiles.", status: "Active" },
    { name: "OpenAlex", role: "Fully open bibliographic catalog of global scholarly knowledge and venues.", status: "Active" },
  ];

  return (
    <div className="space-y-6">
      {/* Intro Header */}
      <div className="bg-white dark:bg-[#1F1F24] border-[2.5px] border-black rounded-2xl shadow-[6px_6px_0px_#111] p-6 sm:p-7">
        <div className="inline-block bg-[#EBB13E] text-black border-2 border-black rounded-lg px-2.5 py-0.5 font-mono text-xs font-black mb-3 shadow-[2px_2px_0px_#111]">
          ARCHITECTURE & PIPELINE
        </div>
        <h2 className="font-black text-2xl sm:text-3xl text-neutral-900 dark:text-neutral-100 font-display">
          How CitationGuard Verifies References
        </h2>
        <p className="font-mono text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 mt-2 max-w-3xl leading-relaxed font-medium">
          CitationGuard operates an end-to-end verification pipeline designed to detect fabricated citations, mismatched DOIs, corrupted author lists, and incorrect venues generated by LLMs.
        </p>
      </div>

      {/* Multi-Source Index Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {sources.map((s, i) => (
          <div key={i} className="p-4 bg-white dark:bg-[#1F1F24] border-2 border-black rounded-2xl shadow-[4px_4px_0px_#111] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-black text-base font-display text-neutral-900 dark:text-neutral-100">{s.name}</span>
                <span className="font-mono text-[10px] font-black px-2.5 py-0.5 rounded-lg bg-[#D1FAE5] text-[#065F46] border-2 border-black shadow-[1px_1px_0px_#111]">
                  {s.status}
                </span>
              </div>
              <p className="font-mono text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed font-medium">
                {s.role}
              </p>
            </div>
            <div className="mt-3 pt-2 border-t-2 border-black/10 dark:border-white/10 font-mono text-[11px] text-neutral-500 font-bold">
              API Federated Lookup
            </div>
          </div>
        ))}
      </div>

      {/* 7-Step Pipeline 3D Flowchart Section */}
      <div className="bg-white dark:bg-[#1F1F24] border-[2.5px] border-black rounded-2xl shadow-[6px_6px_0px_#111] p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-8 border-b-2 border-black">
          <div>
            <h3 className="font-black text-xl sm:text-2xl text-neutral-900 dark:text-neutral-100 font-display uppercase tracking-tight">
              Verification Flowchart Steps
            </h3>
            <p className="font-mono text-xs text-neutral-500 dark:text-neutral-400 mt-0.5 font-medium">
              Sequential multi-stage verification architecture
            </p>
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#EBB13E] border-2 border-black rounded-xl font-mono text-xs font-black shadow-[2px_2px_0px_#111] text-black">
            <span>⚡</span>
            <span>7 Automated Stages</span>
          </div>
        </div>

        {/* Vertical Flowchart Container */}
        <div className="relative max-w-4xl mx-auto py-2">
          {steps.map((step, idx) => {
            const isLast = idx === steps.length - 1;

            return (
              <div key={idx} className="relative">
                {/* 3D Flowchart Step Card */}
                <div
                  className={`flowchart-3d-card group relative bg-gradient-to-br ${step.cardBg} border-[2.5px] border-black rounded-2xl ${step.shadowStyle} ${step.hoverGlow} p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-6 overflow-hidden cursor-default transition-all`}
                >
                  {/* Left 3D Accent Indicator Bar */}
                  <div
                    className={`absolute left-0 top-0 bottom-0 w-2.5 ${step.accentBar} border-r-2 border-black`}
                  />

                  {/* 3D Extruded Numbered Badge */}
                  <div className="pl-1 sm:pl-2 shrink-0">
                    <div
                      className={`w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br ${step.badgeGradient} border-2 border-black shadow-[3px_3px_0px_#111] flex flex-col items-center justify-center font-mono font-black shrink-0 relative overflow-hidden group-hover:scale-105 transition-transform duration-200`}
                    >
                      {/* Top bevel highlight */}
                      <div className="absolute top-0 left-0 right-0 h-1 bg-white/40" />
                      <span className="text-lg sm:text-xl leading-none">
                        {step.num}
                      </span>
                      <span className="text-[9px] uppercase tracking-wider opacity-80 mt-0.5 font-black">
                        Stage
                      </span>
                    </div>
                  </div>

                  {/* Content Body */}
                  <div className="flex-1 min-w-0 pr-1">
                    <div className="flex flex-wrap items-center gap-2.5 mb-2">
                      <h4 className="font-black text-base sm:text-lg text-neutral-900 dark:text-neutral-100 font-display tracking-tight">
                        {step.title}
                      </h4>
                      <span
                        className={`px-2.5 py-0.5 rounded-xl border-2 font-mono text-[10px] sm:text-[11px] font-black uppercase shadow-[1.5px_1.5px_0px_#111] ${step.badgeColor}`}
                      >
                        {step.badge}
                      </span>
                    </div>

                    <p className="font-mono text-xs sm:text-[13px] text-neutral-700 dark:text-neutral-300 leading-relaxed font-medium">
                      {step.desc}
                    </p>
                  </div>
                </div>

                {/* Visible 3D Vertical Connector Between Steps */}
                {!isLast && (
                  <div className="flex flex-col items-center justify-center my-1 select-none py-1">
                    {/* Upper conduit */}
                    <div className="relative w-1.5 h-4 sm:h-5 bg-black dark:bg-neutral-500 rounded-full overflow-hidden">
                      <div className="connector-beam absolute left-0 w-full h-4 bg-gradient-to-b from-transparent via-[#EBB13E] to-transparent rounded-full opacity-90" />
                    </div>

                    {/* 3D Directional Node with down arrow */}
                    <div className="relative z-10 w-7 h-7 rounded-full bg-[#EBB13E] border-2 border-black shadow-[2px_2px_0px_#111] flex items-center justify-center text-neutral-900 my-0.5 transform hover:scale-110 transition-transform">
                      <svg
                        className="w-3.5 h-3.5 stroke-[3]"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M19 14l-7 7m0 0l-7-7m7 7V3"
                        />
                      </svg>
                    </div>

                    {/* Lower conduit */}
                    <div className="relative w-1.5 h-4 sm:h-5 bg-black dark:bg-neutral-500 rounded-full overflow-hidden">
                      <div className="connector-beam absolute left-0 w-full h-4 bg-gradient-to-b from-transparent via-[#EBB13E] to-transparent rounded-full opacity-90" />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
