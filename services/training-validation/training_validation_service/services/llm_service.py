import os
import logging
from datetime import datetime
from openai import OpenAI
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class LLMService:
    """
    A service to interact with a Large Language Model via OpenRouter for validation tasks.
    """
    def __init__(self):
        """Initialize the LLM service with OpenRouter configuration.
        
        Environment Variables:
            OPENROUTER_API_KEY: Your OpenRouter API key (optional for testing)
            OPENROUTER_MODEL: The default model to use (defaults to "openai/gpt-4o")
        """
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            logger.warning("OPENROUTER_API_KEY not set - LLM service will return mock responses for testing")
            self.client = None
            self.default_model = "mock-model"
        else:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            self.default_model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o")

    def get_json_validation(self, prompt: str, context: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends a prompt and a document context to the specified OpenRouter model
        and asks for a structured JSON response for validation.

        Args:
            prompt: The detailed system prompt for the validation task.
            context: The document content to be analyzed.
            model: The model to use via OpenRouter (e.g., "openai/gpt-4o", "anthropic/claude-3.5-sonnet").
                   If not provided, uses the default model from OPENROUTER_MODEL env var.

        Returns:
            A dictionary parsed from the LLM's JSON response.
            
        Raises:
            ValueError: If the response cannot be parsed as JSON or is invalid
            Exception: For any other errors during the API call
        """
        model = model or self.default_model
        
        if not self.client:
            logger.info("Returning mock validation response - no OPENROUTER_API_KEY configured")
            return {
                "status": "Met",
                "gaps": [],
                "recommendations": ["Mock validation - configure OPENROUTER_API_KEY for real validation"],
                "confidence_score": 0.5,
                "_metadata": {
                    "model": "mock-model",
                    "service": "mock",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Here is the document content to analyze:\n\n---\n{context}\n---"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0,  # Set to 0 for maximum fact-based consistency
                extra_headers={
                    "HTTP-Referer": "https://enhanced-ai-agent-os.com",
                    "X-Title": "Training Validation Service",
                }
            )
            
            # Validate and parse the response
            if not response.choices or not response.choices[0].message.content:
                raise ValueError("Empty or invalid response from LLM")
                
            result = json.loads(response.choices[0].message.content)
            
            # Add metadata about the model used
            if isinstance(result, dict):
                result["_metadata"] = {
                    "model": model,
                    "service": "openrouter",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            return result
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Error during LLM validation with model {model}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e

llm_service = LLMService()
