from abc import ABC, abstractmethod
from django.conf import settings
from .models import QueryRecord
import json
import logging

logger = logging.getLogger(__name__)


class AIProviderClient(ABC):
    """Abstract base class for AI provider clients"""
    
    @abstractmethod
    def analyze_query(self, prompt: str, model: str) -> str:
        pass

class MistralClient(AIProviderClient):
    def __init__(self, api_key: str):
        from openai import OpenAI
        self.client = OpenAI(
            base_url="https://api.mistral.ai/v1/",
            api_key=api_key
        )
    
    def analyze_query(self, prompt: str, model: str) -> str:
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

class OpenAIClient(AIProviderClient):
    def __init__(self, api_key: str):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
    
    def analyze_query(self, prompt: str, model: str) -> str:
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

class AnthropicClient(AIProviderClient):
    def __init__(self, api_key: str):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
    
    def analyze_query(self, prompt: str, model: str) -> str:
        response = self.client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

class QueryOptimizerAI:
    def __init__(self):
        """
        Initialize the query optimizer with the config from QUERY_OPTIMIZER_CONFIG in settings.py
        """
        self.config = getattr(settings, 'QUERY_OPTIMIZER_CONFIG', None)
        if not self.config:
            raise ValueError("QUERY_OPTIMIZER_CONFIG is not set in settings.py")

        self.provider = self.config.get('provider', None)
        self.model = self.config.get('model', None)
        self.api_key = self.config.get('api_key', None)
        self.client = None
        self._check_config()
        self._setup_client()
    
    def _check_config(self):
        """Check if the config is valid"""
        if not self.provider in ['mistral', 'openai', 'anthropic']:
            raise ValueError("Invalid provider: {self.provider} we only support mistral, openai, and anthropic")
        
        if not self.model:
            raise ValueError("model is not set in QUERY_OPTIMIZER_CONFIG, please set the model in the QUERY_OPTIMIZER_CONFIG in settings.py")
        
        if not self.api_key:
            raise ValueError("api_key is not set in QUERY_OPTIMIZER_CONFIG, please set the api_key in the QUERY_OPTIMIZER_CONFIG in settings.py")

        
    def _setup_client(self):
        """Initialize the client based on the provider"""
        if self.provider == "mistral":
            self.client = MistralClient(self.api_key)
        elif self.provider == "openai":
            self.client = OpenAIClient(self.api_key)
        elif self.provider == "anthropic":
            self.client = AnthropicClient(self.api_key)
        
        if not self.client:
            raise ValueError(f"Failed to initialize client for provider: {self.provider}, please check the provider in the QUERY_OPTIMIZER_CONFIG in settings.py")
    
    def analyze_query(self, query_record: QueryRecord) -> dict:
        """Analyze a query record and return optimization suggestions"""           
        prompt = self._build_optimization_prompt(query_record)

        try:
            analysis = self.client.analyze_query(prompt, self.model)
            return self._parse_ai_response(analysis)
        except Exception as e:
            logger.info(f"AI analysis failed with {self.provider}: {e}")
            return None
    
    def _build_optimization_prompt(self, query_record: QueryRecord) -> str:
        """Build the optimization prompt for the AI"""
        return f"""
        Analyze this SQL query for potential optimizations:
        
        Query: {query_record.query}
        Execution Time: {query_record.duration} seconds
        Context: {query_record.stack_trace[-500:] if query_record.stack_trace else 'No context'}
        
        Please provide:
        1. A detailed analysis of the query performance issues
        2. Specific optimization suggestions
        3. Rewritten optimized query if applicable
        4. Index suggestions if applicable
        5. Any Django ORM improvements if the query comes from Django
        
        Format your response as JSON with these keys:
        - analysis
        - optimization_suggestions
        - optimized_query (if applicable)
        - index_suggestions
        - django_orm_improvements (if applicable)
        """
    
    def _parse_ai_response(self, response_text: str) -> dict:
        """Parse the AI response into a structured format"""
        try:
            # Handle markdown code blocks
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            # Fallback to treating the entire response as the analysis
            return {
                "analysis": response_text,
                "optimization_suggestions": "",
                "optimized_query": "",
                "index_suggestions": "",
                "django_orm_improvements": ""
            }
