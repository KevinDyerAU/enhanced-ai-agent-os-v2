import os
from openai import OpenAI
from typing import Dict, Any
import json

class LLMService:
    """
    A service to interact with a Large Language Model via OpenRouter for validation tasks.
    """
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
        )

    def get_json_validation(self, prompt: str, context: str, model: str = "openai/gpt-4o") -> Dict[str, Any]:
        """
        Sends a prompt and a document context to the specified OpenRouter model
        and asks for a structured JSON response for validation.

        Args:
            prompt: The detailed system prompt for the validation task.
            context: The document content to be analyzed.
            model: The model to use via OpenRouter (e.g., "openai/gpt-4o", "anthropic/claude-3.5-sonnet").

        Returns:
            A dictionary parsed from the LLM's JSON response.
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Here is the document content to analyze:\n\n---\n{context}\n---"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0, # Set to 0 for maximum fact-based consistency
                extra_headers={
                    "HTTP-Referer": "https://enhanced-ai-agent-os.com", # Replace with your actual site URL
                    "X-Title": "Training Validation Service", # Replace with your app name
                }
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error during LLM validation with model {model}: {e}")
            return {"status": "Error", "detail": str(e)}

llm_service = LLMService()
