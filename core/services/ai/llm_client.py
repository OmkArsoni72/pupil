import os
import google.generativeai as genai
from langchain_community.chat_models import ChatOpenAI
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
            "gemini_1.5_flash": self._gemini_1_5_flash_client,
            "gemini_2.5_flash": self._gemini_2_5_flash_client,
            "gemini_2.5_pro": self._gemini_2_5_pro_client,
            "openai": self._openai_client,
        }

    def get_client(self, model_name: str = "gemini_2.5_flash"):
        if not model_name or model_name not in self.models:
            model_name = "gemini_2.5_flash"
        return self.models[model_name]()

    def _openai_client(self):
        # Pull key from env for OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        return ChatOpenAI(model_name="gpt-4", temperature=0.7, openai_api_key=openai_api_key)

    def _gemini_1_5_flash_client(self):
        return GeminiClient(model_name="gemini-2.5-flash", temperature=0.7)

    def _gemini_2_5_flash_client(self):
        return GeminiClient(model_name="gemini-2.5-flash", temperature=0.6)

    def _gemini_2_5_pro_client(self):
        return GeminiClient(model_name="gemini-2.5-pro", temperature=0.5)

# Usage example:
llm_factory = LLMFactory()

# No environment or model provided, defaults to Gemini 1.5 Flash
llm = llm_factory.get_client()

# Or explicitly specify:
# llm_openai = llm_factory.get_client("openai")
llm_gemini_pro = llm_factory.get_client("gemini_2.5_pro")
