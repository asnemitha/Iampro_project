import { useState } from "react";

import CitationTable from "../components/CitationTable";
import api from "../services/api";
import Navbar from "../components/Navbar";
import PromptInput from "../components/PromptInput";
import PromptAnalysis from "../components/PromptAnalysis";
import LLMResponse from "../components/LLMResponse";
import Loading from "../components/Loading";

export default function Home() {

    const [prompt, setPrompt] = useState("");

    const [loading, setLoading] = useState(false);

    const [result, setResult] = useState(null);

    async function analyze() {

        if (!prompt.trim()) return;

        setLoading(true);

        try {

            const response = await api.post("/analyze", {
                prompt
            });

            setResult(response.data);

        } catch (err) {

    console.error(err);

    if (err.response) {
        alert(`API Error ${err.response.status}: ${JSON.stringify(err.response.data)}`);
    } else {
        alert(err.message);
    }
}

        setLoading(false);
    }

    return (

        <>

            <Navbar />

            <div className="container">

                <div className="left-panel">

                    <PromptInput
                        prompt={prompt}
                        setPrompt={setPrompt}
                        analyze={analyze}
                        loading={loading}
                    />

                </div>

                <div className="right-panel">

                    {loading && <Loading />}

                    {!loading && result && (

                        <>

                            <PromptAnalysis
                                analysis={result.prompt_analysis}
                            />

                            <LLMResponse
                                response={result.llm_response}
                            />

                            <CitationTable
                                citations={result.citation_analysis}
                            />

                        </>

                    )}

                </div>

            </div>

        </>

    );
}