export default function PromptInput({
    prompt,
    setPrompt,
    analyze,
    loading,
}) {
    return (
        <div className="card">

            <h2>Enter Prompt</h2>

            <textarea
                rows={10}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask the LLM anything..."
            />

            <button
                onClick={analyze}
                disabled={loading}
            >
                {loading ? "Analyzing..." : "Analyze"}
            </button>

        </div>
    );
}