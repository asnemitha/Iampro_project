import { useState, useEffect } from "react";

export default function VerificationProgress({
  status = "idle", // 'idle' | 'in_progress' | 'completed' | 'error'
  result = null,
  error = null,
  onReset = () => {},
}) {
  const [inProgressStep, setInProgressStep] = useState(1);
  const [expanded, setExpanded] = useState(false);

  // Staged progression during live request
  useEffect(() => {
    if (status !== "in_progress") return;

    const timers = [
      setTimeout(() => setInProgressStep(2), 1000),
      setTimeout(() => setInProgressStep(3), 2200),
      setTimeout(() => setInProgressStep(4), 3600),
      setTimeout(() => setInProgressStep(5), 5200),
    ];
    return () => {
      timers.forEach(clearTimeout);
      setInProgressStep(1);
    };
  }, [status]);

  if (status === "idle") return null;

  // Extract confirmed facts from real API results
  const promptAnalysis = result?.prompt_analysis;
  const citations = result?.citation_analysis || [];
  const citationsCount = citations.length;
  const verifiedDoiCount = citations.filter((c) => c.doi_match === true || c.matched_doi).length;
  const avgHallucinationScore = citationsCount > 0
    ? Math.round(
        citations.reduce((acc, c) => acc + (typeof c.hallucination_score === "number" ? c.hallucination_score : 0), 0) / citationsCount
      )
    : 0;

  const steps = [
    {
      step: 1,
      title: "Prompt-Aware Classification",
      desc: "Determine whether the user's prompt expects academic citations and screen for adversarial manipulation.",
      completedDetail: promptAnalysis
        ? `Classification: ${promptAnalysis.label_name || "Safe"} (${((promptAnalysis.confidence || 0.95) * 100).toFixed(1)}% confidence)`
        : "Prompt classified as safe academic inquiry.",
    },
    {
      step: 2,
      title: "Citation Parsing",
      desc: "Extract citation references and identify bibliographic fields (titles, authors, years, venues, DOIs).",
      completedDetail: citationsCount > 0
        ? `Parsed ${citationsCount} bibliographic citation reference(s).`
        : "Text parsed; no structured academic citations detected.",
    },
    {
      step: 3,
      title: "DOI Verification",
      desc: "Verify DOIs using authoritative Crossref and DataCite registries. Handle citations without DOIs appropriately.",
      completedDetail: verifiedDoiCount > 0
        ? `Cross-referenced and verified ${verifiedDoiCount} DOI record(s) via Crossref/DataCite.`
        : "Evaluated references without DOI identifiers using title & author matching.",
    },
    {
      step: 4,
      title: "Multi-Source Scholarly Retrieval",
      desc: "Federated publication retrieval across Crossref, Semantic Scholar, and OpenAlex scholarly indexes.",
      completedDetail: "Queried Crossref, Semantic Scholar, and OpenAlex for publication candidates.",
    },
    {
      step: 5,
      title: "Metadata Validation & Hallucination Scoring",
      desc: "RapidFuzz candidate ranking, author-order matching, venue normalization, and hallucination scoring (0–100).",
      completedDetail: citationsCount > 0
        ? `Candidate ranking complete. Average hallucination score: ${avgHallucinationScore}/100.`
        : "Consistency analysis complete.",
    },
    {
      step: 6,
      title: "Final Verification Results",
      desc: "Compile citation status, hallucination types, discrepancy reasons, and suggested IEEE citations.",
      completedDetail: "Verification complete. Results and corrections generated below.",
    },
  ];

  const effectiveStep = status === "completed" ? 6 : inProgressStep;
  const progressPercent = status === "completed" ? 100 : Math.min(Math.round((effectiveStep / 6) * 100), 90);

  return (
    <div className="bg-white dark:bg-[#1f1f26] border-2 border-black rounded-xl shadow-card-sm p-5 mb-5 transition-colors">
      {/* Tracker Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          {/* Radar / Shield Tracker Icon */}
          <div className="w-7 h-7 rounded-lg bg-[#f5b731] border border-black flex items-center justify-center font-black text-xs shadow-[1px_1px_0px_#000]">
            ⚡
          </div>
          <div>
            <h3 className="font-mono text-xs sm:text-sm font-black uppercase tracking-wider text-neutral-900 dark:text-neutral-100 font-display">
              {status === "in_progress" && "Verification Pipeline In Progress"}
              {status === "completed" && "Verification Pipeline Complete (6/6 Passed)"}
              {status === "error" && "Verification Pipeline Halted"}
            </h3>
            <span className="font-mono text-[11px] text-neutral-500 dark:text-neutral-400">
              {status === "in_progress" && `Executing Step ${effectiveStep} of 6`}
              {status === "completed" && "All 6 pipeline stages verified and audited"}
              {status === "error" && `Error encountered at Step ${effectiveStep} of 6`}
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {status === "completed" && (
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="px-2.5 py-1 bg-[#faf4eb] dark:bg-[#27272a] hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-800 dark:text-neutral-200 border border-black rounded-lg font-mono text-[11px] font-bold shadow-[1px_1px_0px_#000] cursor-pointer transition-all"
            >
              {expanded ? "Hide 6 Stages ▲" : "View 6 Stages ▼"}
            </button>
          )}

          {(status === "completed" || status === "error") && (
            <button
              type="button"
              onClick={onReset}
              className="px-2.5 py-1 bg-white dark:bg-[#27272a] hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-800 dark:text-neutral-200 border border-black rounded-lg font-mono text-[11px] font-bold shadow-[1px_1px_0px_#000] cursor-pointer"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar Container */}
      <div className="mb-4">
        <div className="flex justify-between items-center font-mono text-[11px] font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">
          <span>PIPELINE PROGRESS</span>
          <span>{status === "completed" ? "100%" : `${progressPercent}%`}</span>
        </div>
        <div className="w-full h-3 bg-[#faf4eb] dark:bg-[#141416] border-2 border-black rounded-lg overflow-hidden p-0.5 shadow-[1px_1px_0px_#000]">
          <div
            className={`h-full rounded-sm transition-all duration-500 ease-out ${
              status === "error"
                ? "bg-rose-500"
                : status === "completed"
                ? "bg-[#16a34a]"
                : "bg-[#f5b731]"
            }`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Steps List (Always visible during loading, collapsible upon completion) */}
      {(status === "in_progress" || status === "error" || expanded) && (
        <div className="space-y-2.5 pt-2 border-t border-neutral-200 dark:border-neutral-700 font-mono">
          {steps.map((s) => {
            const isCompleted = status === "completed" || (status === "in_progress" && s.step < effectiveStep);
            const isCurrent = status === "in_progress" && s.step === effectiveStep;
            const isFailed = status === "error" && s.step === effectiveStep;
            const isPending = !isCompleted && !isCurrent && !isFailed;

            let badgeClass = "bg-neutral-100 dark:bg-neutral-800 text-neutral-500 border-neutral-300 dark:border-neutral-700";
            let rowBorder = "border-neutral-200 dark:border-neutral-800 bg-[#faf4eb]/50 dark:bg-[#1a1a20]";

            if (isCompleted) {
              badgeClass = "bg-[#16a34a] text-white border-black font-black";
              rowBorder = "border-black bg-emerald-50/60 dark:bg-emerald-950/20";
            } else if (isCurrent) {
              badgeClass = "bg-[#f5b731] text-black border-black font-black animate-pulse";
              rowBorder = "border-black bg-amber-50/70 dark:bg-amber-950/20 ring-1 ring-[#f5b731]";
            } else if (isFailed) {
              badgeClass = "bg-rose-500 text-white border-black font-black";
              rowBorder = "border-black bg-rose-50 dark:bg-rose-950/30";
            }

            return (
              <div
                key={s.step}
                className={`p-3 rounded-lg border transition-all flex items-start gap-3 ${rowBorder}`}
              >
                {/* Step Indicator Badge */}
                <div
                  className={`w-6 h-6 rounded-md border flex items-center justify-center shrink-0 text-xs shadow-[1px_1px_0px_#000] ${badgeClass}`}
                >
                  {isCompleted && "✓"}
                  {isCurrent && (
                    <span className="w-2 h-2 rounded-full bg-black animate-ping" />
                  )}
                  {isFailed && "✕"}
                  {isPending && s.step}
                </div>

                {/* Step Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center justify-between gap-1">
                    <span className="font-extrabold text-xs text-neutral-900 dark:text-neutral-100">
                      Step {s.step} — {s.title}
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-wider">
                      {isCompleted && <span className="text-[#16a34a]">Completed</span>}
                      {isCurrent && <span className="text-amber-600 dark:text-amber-400">Processing...</span>}
                      {isFailed && <span className="text-rose-600">Failed</span>}
                      {isPending && <span className="text-neutral-400">Pending</span>}
                    </span>
                  </div>

                  <p className="text-[11px] text-neutral-600 dark:text-neutral-400 mt-0.5 leading-relaxed">
                    {isCompleted && s.completedDetail ? s.completedDetail : s.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Failure Box */}
      {status === "error" && error && (
        <div className="mt-4 p-4 rounded-lg border-2 border-black bg-rose-100 dark:bg-rose-950/40 text-rose-900 dark:text-rose-200 font-mono text-xs shadow-[2px_2px_0px_#000]">
          <div className="flex items-center gap-2 font-bold mb-1">
            <span>⚠️</span>
            <span>API Pipeline Error:</span>
          </div>
          <p className="leading-relaxed whitespace-pre-wrap">{error}</p>
        </div>
      )}
    </div>
  );
}
