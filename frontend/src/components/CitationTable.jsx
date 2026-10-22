export default function CitationTable({ citations }) {

    if (!citations || citations.length === 0)
        return null;

    function badge(score) {

        if (score === null || score === undefined || typeof score !== "number")
            return "medium";

        if (score <= 20)
            return "good";

        if (score <= 50)
            return "medium";

        return "bad";
    }

    return (

        <div className="card">

            <h2>Citation Analysis</h2>

            {citations.map((citation, index) => (

                <div
                    key={index}
                    className="citation-card"
                >

                    <h3>

                        Citation {index + 1}

                    </h3>

                    <p>

                        <b>Exists:</b>

                        {" "}

                        {citation.paper_exists === true ? "Yes" : citation.paper_exists === false ? "No" : "Unverified"}

                    </p>

                    <p>

                        <b>Hallucination Type:</b>

                        {" "}

                        {citation.hallucination_type || "N/A"}

                    </p>

                    <p>

                        <b>Hallucination Score:</b>

                        <span className={badge(citation.hallucination_score)}>

                            {" "}

                            {citation.hallucination_score !== null && citation.hallucination_score !== undefined ? citation.hallucination_score : "N/A"}

                        </span>

                    </p>

                    <p>

                        <b>Confidence:</b>

                        {" "}

                        {citation.confidence}

                    </p>

                    <p>

                        <b>Reason:</b>

                    </p>

                    <ul>

                        {citation.reason?.map((r, i) => (

                            <li key={i}>{r}</li>

                        ))}

                    </ul>

                    {citation.prompt_consistency && citation.prompt_consistency.checked && (
                        <div style={{
                            marginTop: "12px",
                            marginBottom: "12px",
                            padding: "10px 14px",
                            borderRadius: "6px",
                            backgroundColor: citation.prompt_consistency.matches ? "#f0fdf4" : "#fefce8",
                            border: `1px solid ${citation.prompt_consistency.matches ? "#bbf7d0" : "#fef08a"}`
                        }}>
                            <p style={{ margin: "0 0 6px 0", fontWeight: "600", fontSize: "0.95em", color: citation.prompt_consistency.matches ? "#166534" : "#854d0e" }}>
                                <b>Prompt Consistency:</b>{" "}
                                {citation.prompt_consistency.matches ? "Matches Prompt Metadata" : "Prompt Metadata Mismatch"}
                            </p>
                            <p style={{ margin: 0, fontSize: "0.9em", color: citation.prompt_consistency.matches ? "#15803d" : "#a16207" }}>
                                {citation.prompt_consistency.explanation}
                            </p>
                        </div>
                    )}

                    {citation.corrected_citation ? (

                        <>

                            <hr />

                            <p>

                                <b>Suggested Citation</b>

                            </p>

                            <pre>

                                {citation.corrected_citation}

                            </pre>

                        </>

                    ) : (

                        <>

                            <hr />

                            <p>

                                <b>Suggested Citation</b>

                            </p>

                            <pre>

                                No reliable correction found.

                            </pre>

                        </>

                    )}

                </div>

            ))}

        </div>

    );

}