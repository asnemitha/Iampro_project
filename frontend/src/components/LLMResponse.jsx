export default function LLMResponse({ response }) {

    if (!response) return null;

    return (

        <div className="card">

            <h2>LLM Response</h2>

            <pre>

                {response}

            </pre>

        </div>

    );
}