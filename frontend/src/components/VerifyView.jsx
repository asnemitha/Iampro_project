import PromptInput from "./PromptInput";
import VerificationProgress from "./VerificationProgress";
import VerificationSummary from "./VerificationSummary";
import ResponseTabs from "./ResponseTabs";
import CorrectionsAudit from "./CorrectionsAudit";
import PromptAnalysis from "./PromptAnalysis";
import CitationTable from "./CitationTable";

export default function VerifyView({
  prompt,
  setPrompt,
  llmOutput,
  setLlmOutput,
  analyze,
  loading,
  result,
  setResult,
  error,
  setError,
  onLoadExample,
  onClear,
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-start">
      {/* LEFT COLUMN — INPUT CITATIONS (~42% width) */}
      <div className="lg:col-span-5">
        <PromptInput
          prompt={prompt}
          setPrompt={setPrompt}
          llmOutput={llmOutput}
          setLlmOutput={setLlmOutput}
          analyze={analyze}
          loading={loading}
          onLoadExample={onLoadExample}
          onClear={onClear}
        />
      </div>

      {/* RIGHT COLUMN — RESULTS & PIPELINE EXECUTION (~58% width) */}
      <div className="lg:col-span-7 bg-white dark:bg-[#1F1F24] border-[2.5px] border-black rounded-2xl shadow-[6px_6px_0px_#111] p-6 sm:p-7 min-h-[500px] flex flex-col justify-start transition-colors">
        {loading && (
          <VerificationProgress status="in_progress" />
        )}

        {error && !loading && (
          <VerificationProgress
            status="error"
            error={error}
            onReset={() => setError(null)}
          />
        )}

        {!loading && !result && !error && (
          /* Empty State — Exact replica of the reference screenshot */
          <div className="flex flex-col items-center justify-center text-center py-12 px-4 my-auto select-none">
            
            {/* Decorative Search Icon Container */}
            <div className="relative mb-5">
              
              {/* Top-Right Tab Accent */}
              <div className="absolute -top-2.5 right-2 w-5 h-2.5 bg-[#EBB13E] border-t-2 border-l-2 border-r-2 border-black rounded-t-sm z-0" />

              {/* Bottom-Left 3x3 Dotted Pattern */}
              <div className="absolute -bottom-2 -left-2 grid grid-cols-3 gap-1 z-0">
                {[...Array(9)].map((_, i) => (
                  <span key={i} className="w-1 h-1 rounded-full bg-neutral-900" />
                ))}
              </div>

              {/* Main Golden Card */}
              <div className="relative z-10 w-20 h-20 rounded-2xl bg-[#EBB13E] border-2 border-black shadow-[4px_4px_0px_#111] flex items-center justify-center">
                <svg 
                  className="w-10 h-10 text-neutral-900 stroke-[2.4]" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" 
                  />
                </svg>
              </div>
            </div>

            {/* Headline */}
            <h3 className="font-black text-2xl text-neutral-900 dark:text-neutral-100 tracking-tight font-display mb-2">
              Paste a response to begin
            </h3>

            {/* Description */}
            <p className="font-mono text-xs sm:text-[13px] text-neutral-600 dark:text-neutral-400 text-center max-w-sm leading-relaxed mb-6">
              Enter your academic query and model output on the left, or pick one of the preset test cases using the &quot;Load Example&quot; button.
            </p>

            {/* Bottom Chip */}
            <div className="inline-flex items-center gap-2 bg-white dark:bg-[#27272a] border-2 border-black rounded-xl px-4 py-2 shadow-[2.5px_2.5px_0px_#111]">
              <span className="text-sm">📖</span>
              <span className="font-mono text-xs font-black text-neutral-900 dark:text-neutral-100 tracking-wider">
                ICDDS 2026 Author + Venue Algorithm
              </span>
            </div>

          </div>
        )}

        {!loading && result && (
          <div className="space-y-5">
            {/* 1. Six-Step Verification Pipeline Tracker (Completed Audit State) */}
            <VerificationProgress
              status="completed"
              result={result}
              onReset={() => setResult(null)}
            />

            {/* 2. Prompt Safety Analysis */}
            <PromptAnalysis analysis={result.prompt_analysis} />

            {/* 3. 4-Stat Metric Summary Tiles & End-to-End Status */}
            {result.verification_summary && (
              <VerificationSummary summary={result.verification_summary} citations={result.citation_analysis} />
            )}

            {/* 4. Final Re-verified Trustworthy Response */}
            <ResponseTabs
              finalResponse={result.final_response || result.llm_response}
              originalResponse={result.original_response || result.llm_response}
              hasCorrections={Boolean(result.applied_corrections && result.applied_corrections.length > 0)}
              unresolvedCount={result.verification_summary?.unresolved_count || 0}
            />

            {/* 5. Applied Corrections Audit Trail (if corrections were made) */}
            {result.applied_corrections && result.applied_corrections.length > 0 && (
              <CorrectionsAudit corrections={result.applied_corrections} />
            )}

            {/* 6. Citations Analysis with Filter Pills, Segmented Risk Meter & Integrity Checks */}
            <CitationTable
              citations={result.citation_analysis}
              initialCitations={result.initial_citation_analysis}
              appliedCorrections={result.applied_corrections}
            />
          </div>
        )}

      </div>
    </div>
  );
}
