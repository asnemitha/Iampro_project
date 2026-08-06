from app.services.gemini_service import generate_response


class PipelineController:
    """
    Main controller for the CiteGuard pipeline.
    Every research module will be added here step by step.
    """

    def run(self, prompt: str):

        # Step 1 (Temporary)
        response = generate_response(prompt)

        return {
            "user_prompt": prompt,
            "llm_response": response
        }