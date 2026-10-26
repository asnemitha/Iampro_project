import { useState } from "react";

export default function BenchmarkView() {
  const [selectedConfig, setSelectedConfig] = useState("all");

  const benchmarkConfigs = [
    {
      id: "baseline",
      name: "Baseline CiteGuard",
      accuracy: "79.67%",
      precision: "94.16%",
      recall: "80.60%",
      f1: "86.85%",
      tp: 403,
      fp: 25,
      tn: 75,
      fn: 97,
      description: "Standard DOI verification and naive multi-source scholarly retrieval."
    },
    {
      id: "author",
      name: "CiteGuard + Author Validation",
      accuracy: "89.33%",
      precision: "94.86%",
      recall: "92.20%",
      f1: "93.51%",
      tp: 461,
      fp: 25,
      tn: 75,
      fn: 39,
      description: "Adds token-sort Jaro-Winkler author matching and author-order invariant scoring."
    },
    {
      id: "venue",
      name: "CiteGuard + Venue Validation",
      accuracy: "80.67%",
      precision: "94.24%",
      recall: "81.80%",
      f1: "87.58%",
      tp: 409,
      fp: 25,
      tn: 75,
      fn: 91,
      description: "Adds normalized conference acronym & publisher venue matching."
    },
    {
      id: "combined",
      name: "Author + Venue Validation (Best)",
      accuracy: "90.33%",
      precision: "94.92%",
      recall: "93.40%",
      f1: "94.15%",
      tp: 467,
      fp: 25,
      tn: 75,
      fn: 33,
      isBest: true,
      description: "Full dual-pipeline incorporating both author & venue validation. Reduces false negatives from 97 to 33."
    }
  ];

  const categories = [
    { name: "Genuine / Valid Citations", baseline: "75/100", author: "75/100", venue: "75/100", combined: "75/100", count: 100 },
    { name: "Corrupted Authors", baseline: "25/100", author: "83/100", venue: "25/100", combined: "83/100", count: 100 },
    { name: "Wrong Publication Year", baseline: "100/100", author: "100/100", venue: "100/100", combined: "100/100", count: 100 },
    { name: "Wrong Venue / Publisher", baseline: "79/100", author: "79/100", venue: "85/100", combined: "85/100", count: 100 },
    { name: "DOI Mismatch (Fake DOI)", baseline: "99/100", author: "99/100", venue: "99/100", combined: "99/100", count: 100 },
    { name: "Plausible Fabricated", baseline: "100/100", author: "100/100", venue: "100/100", combined: "100/100", count: 100 },
  ];

  const activeMetric = benchmarkConfigs.find(c => c.id === selectedConfig) || benchmarkConfigs[3];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white dark:bg-[#1F1F24] border-[2.5px] border-black rounded-2xl shadow-[6px_6px_0px_#111] p-6 sm:p-7">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-block bg-[#EBB13E] text-black border-2 border-black rounded-lg px-2.5 py-0.5 font-mono text-xs font-black mb-2 shadow-[2px_2px_0px_#111]">
              ICDDS 2026 • PAPER ID: 158
            </div>
            <h2 className="font-black text-2xl sm:text-3xl text-neutral-900 dark:text-neutral-100 font-display">
              Empirical Benchmark Evaluation
            </h2>
            <p className="font-mono text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 mt-1 max-w-2xl font-medium">
              Evaluated on 600 controlled citation instances derived from 100 real computer science papers across 5 alteration categories and genuine controls.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-black px-3 py-1.5 rounded-xl border-2 border-black bg-[#FAF5EC] dark:bg-[#27272a] shadow-[2px_2px_0px_#111]">
              📊 600 Citations
            </span>
            <span className="font-mono text-xs font-black px-3 py-1.5 rounded-xl border-2 border-black bg-[#EBB13E] text-black shadow-[2px_2px_0px_#111]">
              🎯 94.15% F1-Score
            </span>
          </div>
        </div>
      </div>

      {/* Metric Cards Comparison */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {benchmarkConfigs.map((cfg) => {
          const isSelected = selectedConfig === cfg.id || (selectedConfig === "all" && cfg.isBest);
          return (
            <div
              key={cfg.id}
              onClick={() => setSelectedConfig(cfg.id)}
              className={`p-5 rounded-2xl border-[2.5px] border-black transition-all cursor-pointer ${
                cfg.isBest
                  ? "bg-[#EBB13E] shadow-[6px_6px_0px_#111] text-black"
                  : "bg-white dark:bg-[#1F1F24] shadow-[4px_4px_0px_#111] text-neutral-900 dark:text-neutral-100"
              } ${isSelected ? "ring-2 ring-black" : "hover:-translate-x-0.5 hover:-translate-y-0.5"}`}
            >
              <div className="flex items-center justify-between gap-1 mb-2">
                <span className="font-mono text-[11px] font-black uppercase tracking-wider">
                  {cfg.isBest ? "★ Best Model" : "Ablation"}
                </span>
                <span className="font-mono text-xs font-black">
                  F1: {cfg.f1}
                </span>
              </div>
              <h3 className="font-black text-base mb-3 font-display">
                {cfg.name}
              </h3>

              <div className="space-y-1.5 font-mono text-xs border-t-2 border-black/20 pt-2.5">
                <div className="flex justify-between">
                  <span>Accuracy:</span>
                  <span className="font-black">{cfg.accuracy}</span>
                </div>
                <div className="flex justify-between">
                  <span>Precision:</span>
                  <span className="font-black">{cfg.precision}</span>
                </div>
                <div className="flex justify-between">
                  <span>Recall:</span>
                  <span className="font-black">{cfg.recall}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Breakdown & Confusion Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Category Breakdown Table (2 columns on large) */}
        <div className="lg:col-span-2 bg-white dark:bg-[#1F1F24] border-[2.5px] border-black rounded-2xl shadow-[6px_6px_0px_#111] p-6">
          <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-black">
            <h3 className="font-black text-lg text-neutral-900 dark:text-neutral-100 font-display uppercase">
              Accuracy by Error Category (600 Citations)
            </h3>
            <span className="font-mono text-xs font-black text-neutral-500">
              6 Categories x 100
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b-2 border-black bg-[#FAF5EC] dark:bg-[#27272a]">
                  <th className="py-2.5 px-3 font-black">Category</th>
                  <th className="py-2.5 px-3 font-bold text-center">Baseline</th>
                  <th className="py-2.5 px-3 font-bold text-center">+ Author</th>
                  <th className="py-2.5 px-3 font-bold text-center">+ Venue</th>
                  <th className="py-2.5 px-3 font-black text-center bg-[#EBB13E] text-black">Author + Venue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700">
                {categories.map((cat, idx) => (
                  <tr key={idx} className="hover:bg-neutral-50 dark:hover:bg-neutral-800/40">
                    <td className="py-2.5 px-3 font-bold text-neutral-900 dark:text-neutral-100">
                      {cat.name}
                    </td>
                    <td className="py-2.5 px-3 text-center text-neutral-600 dark:text-neutral-400">
                      {cat.baseline}
                    </td>
                    <td className="py-2.5 px-3 text-center text-neutral-600 dark:text-neutral-400">
                      {cat.author}
                    </td>
                    <td className="py-2.5 px-3 text-center text-neutral-600 dark:text-neutral-400">
                      {cat.venue}
                    </td>
                    <td className="py-2.5 px-3 text-center font-black bg-[#FEF3C7] dark:bg-amber-950/20 text-neutral-900 dark:text-neutral-100">
                      {cat.combined}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 p-3.5 rounded-xl bg-[#FAF5EC] dark:bg-[#27272a] border-2 border-black font-mono text-xs text-neutral-800 dark:text-neutral-200 shadow-[2px_2px_0px_#111]">
            <b>Key finding:</b> Corrupted-author detection increased from 25% (25/100) in the baseline to 83% (83/100) with Author Validation, detecting 58 additional hallucinated citations.
          </div>
        </div>

        {/* 2x2 Confusion Matrix Card */}
        <div className="bg-white dark:bg-[#1F1F24] border-[2.5px] border-black rounded-2xl shadow-[6px_6px_0px_#111] p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b-2 border-black mb-4">
              <h3 className="font-black text-lg text-neutral-900 dark:text-neutral-100 font-display uppercase">
                Confusion Matrix
              </h3>
              <span className="font-mono text-xs font-black px-2.5 py-0.5 rounded-lg bg-[#EBB13E] text-black border-2 border-black shadow-[1.5px_1.5px_0px_#111]">
                {activeMetric.name.split(" ")[0]}
              </span>
            </div>

            <p className="font-mono text-xs text-neutral-600 dark:text-neutral-400 mb-4 font-medium">
              {activeMetric.description}
            </p>

            {/* 2x2 Grid */}
            <div className="grid grid-cols-2 gap-3 font-mono text-xs">
              {/* TP */}
              <div className="p-3.5 rounded-xl border-2 border-black bg-[#D1FAE5] text-[#065F46] shadow-[2.5px_2.5px_0px_#111]">
                <span className="block font-black text-[10px] uppercase">
                  True Positives (TP)
                </span>
                <span className="text-2xl font-black block mt-1">{activeMetric.tp}</span>
                <span className="text-[10px] font-bold opacity-80">Hallucinations Detected</span>
              </div>

              {/* FN */}
              <div className="p-3.5 rounded-xl border-2 border-black bg-[#FFE4E6] text-[#9F1239] shadow-[2.5px_2.5px_0px_#111]">
                <span className="block font-black text-[10px] uppercase">
                  False Negatives (FN)
                </span>
                <span className="text-2xl font-black block mt-1">{activeMetric.fn}</span>
                <span className="text-[10px] font-bold opacity-80">Missed Hallucinations</span>
              </div>

              {/* FP */}
              <div className="p-3.5 rounded-xl border-2 border-black bg-[#FEF3C7] text-[#92400E] shadow-[2.5px_2.5px_0px_#111]">
                <span className="block font-black text-[10px] uppercase">
                  False Positives (FP)
                </span>
                <span className="text-2xl font-black block mt-1">{activeMetric.fp}</span>
                <span className="text-[10px] font-bold opacity-80">Valid Flagged As Fake</span>
              </div>

              {/* TN */}
              <div className="p-3.5 rounded-xl border-2 border-black bg-[#DBEAFE] text-[#1E40AF] shadow-[2.5px_2.5px_0px_#111]">
                <span className="block font-black text-[10px] uppercase">
                  True Negatives (TN)
                </span>
                <span className="text-2xl font-black block mt-1">{activeMetric.tn}</span>
                <span className="text-[10px] font-bold opacity-80">Correctly Verified Real</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t-2 border-black/10 dark:border-white/10 flex justify-between font-mono text-xs">
            <span>Overall Total: <b>600 Instances</b></span>
            <span>Accuracy: <b className="text-emerald-600">{activeMetric.accuracy}</b></span>
          </div>
        </div>

      </div>
    </div>
  );
}
