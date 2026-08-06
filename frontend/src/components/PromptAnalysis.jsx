export default function PromptAnalysis({ analysis }) {

    if (!analysis) return null;

    let badge = "gray";

    if (analysis.label_name === "Safe")
        badge = "green";

    else if (analysis.label_name === "Suspicious")
        badge = "orange";

    else
        badge = "red";

    return (

        <div className="card">

            <h2>Prompt Analysis</h2>

            <h3 className={badge}>
                {analysis.label_name}
            </h3>

            <p>

                Confidence:

                {" "}

                {(analysis.confidence * 100).toFixed(2)}%

            </p>

        </div>

    );
}