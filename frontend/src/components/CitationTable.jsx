export default function CitationTable({ citations }) {

    if (!citations || citations.length === 0)
        return null;

    function badge(score) {

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

                        {citation.paper_exists ? "Yes" : "No"}

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

                            {citation.hallucination_score}

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