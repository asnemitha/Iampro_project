import { useState, useEffect } from "react";
import api from "../services/api";
import Navbar from "../components/Navbar";
import HeroBanner from "../components/HeroBanner";
import VerifyView from "../components/VerifyView";
import BenchmarkView from "../components/BenchmarkView";
import HowItWorksView from "../components/HowItWorksView";
import AboutView from "../components/AboutView";

const PRESET_EXAMPLES = [
  {
    name: "ResNet & YOLO (Computer Vision - Valid)",
    prompt: "Provide the IEEE citation for 'Deep Residual Learning for Image Recognition' by Kaiming He et al. (CVPR 2016) and 'You Only Look Once: Unified, Real-Time Object Detection' by Joseph Redmon et al. (CVPR 2016).",
    llmOutput: "1. Deep Residual Learning for Image Recognition\nAuthors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun\nYear: 2016\nVenue: IEEE Conference on Computer Vision and Pattern Recognition (CVPR)\nDOI: 10.1109/CVPR.2016.90\n\n2. You Only Look Once: Unified, Real-Time Object Detection\nAuthors: Joseph Redmon, Santosh Divvala, Ross Girshick, Ali Farhadi\nYear: 2016\nVenue: IEEE Conference on Computer Vision and Pattern Recognition (CVPR)\nDOI: 10.1109/CVPR.2016.91"
  },
  {
    name: "Attention Is All You Need (Corrupted Authors & Venue)",
    prompt: "Provide the academic reference for 'Attention Is All You Need' with author and publication details.",
    llmOutput: "1. Attention Is All You Need\nAuthors: Geoffrey Hinton, Yann LeCun, Yoshua Bengio\nYear: 2019\nVenue: Nature Machine Intelligence\nDOI: 10.1038/s42256-019-0001-x"
  },
  {
    name: "Quantum Transformers (Plausible Fabricated Citation)",
    prompt: "Provide the citation for 'Quantum Transformer Architectures for Graph Neural Networks' by David Silver and Demis Hassabis.",
    llmOutput: "1. Quantum Transformer Architectures for Graph Neural Networks\nAuthors: David Silver, Demis Hassabis\nYear: 2022\nVenue: IEEE Transactions on Neural Networks and Learning Systems\nDOI: 10.1109/TNNLS.2022.9876543"
  }
];

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [llmOutput, setLlmOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [exampleIndex, setExampleIndex] = useState(0);
  const [toastMessage, setToastMessage] = useState(null);

  // Active tab synchronized with URL (?tab=verify)
  const [activeTab, setActiveTab] = useState(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get("tab");
      if (tabParam && ["verify", "benchmark", "how-it-works", "about"].includes(tabParam)) {
        return tabParam;
      }
    } catch {
      // fallback
    }
    return "verify";
  });

  // Dark/Light Theme state with persistence
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem("citeguard_theme");
      if (saved === "dark" || saved === "light") {
        return saved;
      }
    } catch {
      // fallback
    }
    return "light";
  });

  useEffect(() => {
    try {
      if (theme === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
      localStorage.setItem("citeguard_theme", theme);
    } catch {
      // fallback
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
    try {
      const url = new URL(window.location);
      url.searchParams.set("tab", newTab);
      window.history.pushState({}, "", url);
    } catch {
      // ignore
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleLoadExample = () => {
    const example = PRESET_EXAMPLES[exampleIndex % PRESET_EXAMPLES.length];
    setPrompt(example.prompt);
    setLlmOutput(example.llmOutput);
    setExampleIndex((prev) => prev + 1);
    setResult(null);
    setError(null);

    setToastMessage(`Loaded: ${example.name}`);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleClear = () => {
    setPrompt("");
    setLlmOutput("");
    setResult(null);
    setError(null);
  };

  async function analyze() {
    const currentPrompt = prompt.trim();
    const currentLlmOutput = llmOutput.trim();

    if (!currentPrompt && !currentLlmOutput) return;

    // Clear previous results immediately
    setResult(null);
    setError(null);
    setLoading(true);

    const payload = {
      prompt: currentPrompt || "Verify citations in the provided text.",
    };
    if (currentLlmOutput) {
      payload.llm_response = currentLlmOutput;
    }

    console.log("SUBMITTING TO /analyze:", payload);

    try {
      const response = await api.post("/analyze", payload);
      console.log("RECEIVED RESPONSE:", response.data);
      setResult(response.data);
    } catch (err) {
      console.error("CiteGuard Verification Request Failed:", err);
      setResult(null);

      let errMsg = "An unexpected error occurred while communicating with CiteGuard.";
      if (err.code === "ERR_NETWORK" || err.message === "Network Error") {
        errMsg = `Unable to connect to CiteGuard backend at ${api.defaults.baseURL || "http://127.0.0.1:8000"}. Please ensure the FastAPI server is running (e.g. uvicorn app.main:app --port 8000) and that CORS allows requests from this origin.`;
      } else if (err.code === "ECONNABORTED" || err.message?.includes("timeout")) {
        errMsg = "Verification request timed out. External scholarly data providers (Crossref, Semantic Scholar, OpenAlex) or LLM generation may be experiencing latency.";
      } else if (err.response) {
        const detail = err.response.data?.detail || err.response.data?.message || (typeof err.response.data === "string" ? err.response.data : JSON.stringify(err.response.data));
        errMsg = `Backend Error (HTTP ${err.response.status}): ${detail}`;
      } else if (err.message) {
        errMsg = err.message;
      }
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[var(--bg-cream)] text-neutral-900 dark:text-neutral-100 transition-colors duration-200 flex flex-col justify-between">
      <div>
        {/* Navigation Bar */}
        <Navbar 
          activeTab={activeTab} 
          setActiveTab={handleTabChange} 
          theme={theme} 
          toggleTheme={toggleTheme} 
        />

        {/* Feedback Toast Notification */}
        {toastMessage && (
          <div className="fixed top-24 right-6 z-50 bg-[#f5b731] text-black border-2 border-black rounded-xl px-4 py-2 font-mono text-xs font-black shadow-[3px_3px_0px_#000] flex items-center gap-2 animate-bounce">
            <span>✨</span>
            <span>{toastMessage}</span>
          </div>
        )}

        {/* Main Content Area */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
          
          {/* Hero Banner */}
          <HeroBanner />

          {/* Tab Views */}
          {activeTab === "verify" && (
            <VerifyView
              prompt={prompt}
              setPrompt={setPrompt}
              llmOutput={llmOutput}
              setLlmOutput={setLlmOutput}
              analyze={analyze}
              loading={loading}
              result={result}
              setResult={setResult}
              error={error}
              setError={setError}
              onLoadExample={handleLoadExample}
              onClear={handleClear}
            />
          )}

          {activeTab === "benchmark" && <BenchmarkView />}

          {activeTab === "how-it-works" && <HowItWorksView />}

          {activeTab === "about" && <AboutView />}

        </main>
      </div>

      {/* Footer */}
      <footer className="w-full border-t-[2.5px] border-black bg-[#fbf7ee] dark:bg-[#18181b] mt-12 py-6 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-xs text-neutral-600 dark:text-neutral-400">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-[#f5b731] border border-black inline-block" />
            <span className="font-bold text-neutral-900 dark:text-neutral-100">CitationGuard</span>
            <span>— Prompt-Aware Academic Citation Verification Pipeline</span>
          </div>

          <div className="flex items-center gap-4">
            <span>ICDDS 2026 (Paper #158)</span>
            <span>•</span>
            <span>R V College of Engineering</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
