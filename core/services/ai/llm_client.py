import os
import google.generativeai as genai
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
import asyncio
class GeminiClient:
    def __init__(self, model_name: str, temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            # Fallback to mock for testing/development
            print("WARNING: GEMINI_API_KEY not found. Using mock client for testing.")
            self.model = None
            return
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def chat(self, prompt: str) -> str:
        """Call actual Gemini API and return the response text"""
        if not self.model:
            # Mock response for testing
            return '{"error": "Mock response - GEMINI_API_KEY not configured"}'
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API call failed: {str(e)}")

    async def achat(self, prompt: str) -> str:
        """Async version of chat for compatibility with LangChain"""
        # Run the sync call in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.chat, prompt)

class LLMFactory:
    def __init__(self):
        self.models = {
            "gemini_2.5_flash": self._gemini_2_5_flash_client,
            # Keep alias to avoid breakages if older code passes 1.5 key
            "gemini_1.5_flash": self._gemini_2_5_flash_client,
            # Map any 'pro' requests to flash to enforce single-model policy
            "gemini_2.5_pro": self._gemini_2_5_flash_client,
        }

    def get_client(self, model_name: str = "gemini_2.5_flash"):
        if not model_name or model_name not in self.models:
            model_name = "gemini_2.5_flash"
        return self.models[model_name]()

    def _gemini_2_5_flash_client(self):
        return GeminiClient(model_name="gemini-2.5-flash", temperature=0.6)

# Usage example:
llm_factory = LLMFactory()

# No environment or model provided, defaults to Gemini 2.5 Flash
llm = llm_factory.get_client()

# Or explicitly specify different keys (aliases map to 2.5 flash):
llm_gemini_pro = llm_factory.get_client("gemini_2.5_flash")
