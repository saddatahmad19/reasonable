from dataclasses import dataclass
from typing import Optional, Dict, Any
from langchain_openai import AzureChatOpenAI
from langchain_core.language_models import BaseChatModel
from urllib.parse import urlparse

@dataclass
class LLMConfig:
    """Configuration class for LLM providers
    
    Attributes:
        provider: Which LLM provider to use (e.g., 'azure_openai').
        api_key: API key for the provider.
        endpoint: Full endpoint URL for the Azure OpenAI resource (e.g., 'https://myopenaiinstance.openai.azure.com/').
        deployment_name: Name of the model deployment within your Azure OpenAI instance.
        api_version: Azure OpenAI API version (e.g., '2024-02-01').
        model_name: Underlying model name (e.g., 'gpt-4o', for tracing/token counting only).
        temperature: Sampling temperature for generation.
        max_tokens: Maximum number of tokens to generate.
    """
    provider: str
    api_key: str
    endpoint: Optional[str] = None
    deployment_name: Optional[str] = None
    api_version: Optional[str] = None
    model_name: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.provider == "azure_openai":
            if not all([self.api_key, self.endpoint, self.deployment_name]):
                raise ValueError("Azure OpenAI requires api_key, endpoint, and deployment_name")
        elif self.provider == "openai":
            if not self.api_key:
                raise ValueError("OpenAI requires api_key")
        # Add more provider validations as needed

    @property
    def instance_name(self) -> Optional[str]:
        """Extract the Azure OpenAI instance name from the endpoint URL."""
        if self.endpoint:
            netloc = urlparse(self.endpoint).netloc
            return netloc.split(".")[0] if netloc else None
        return None

class LLMFactory:
    """Factory class to create LLM instances based on configuration"""
    
    @staticmethod
    def create_llm(config: LLMConfig) -> BaseChatModel:
        """Create an LLM instance based on the configuration"""
        
        if config.provider == "azure_openai":
            return LLMFactory._create_azure_openai(config)
        elif config.provider == "openai":
            return LLMFactory._create_openai(config)
        elif config.provider == "gemini":
            return LLMFactory._create_gemini(config)
        elif config.provider == "anthropic":
            return LLMFactory._create_anthropic(config)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    @staticmethod
    def _create_azure_openai(config: LLMConfig) -> AzureChatOpenAI:
        """Create Azure OpenAI instance"""
        kwargs = dict(
            azure_endpoint=config.endpoint,
            api_key=config.api_key,
            api_version=config.api_version or "2024-02-01",
            deployment_name=config.deployment_name,
            temperature=config.temperature,
            streaming=True
        )
        # Determine which token parameter to use
        # Use max_completion_tokens for GPT-4o, o1, o1-preview, o1-series, etc.
        # Use max_tokens for older models
        if config.max_tokens is not None:
            deployment = (config.deployment_name or "").lower()
            model = (config.model_name or "").lower()
            # List of new models that require max_completion_tokens
            new_token_param_models = [
                "gpt-4o", "o1", "o1-preview", "o1-series", "o3", "o3-mini", "o4", "o4-mini"
            ]
            if any(x in deployment for x in new_token_param_models) or any(x in model for x in new_token_param_models):
                kwargs["max_completion_tokens"] = config.max_tokens
            else:
                kwargs["max_tokens"] = config.max_tokens
        if config.model_name:
            kwargs["model_name"] = config.model_name
        return AzureChatOpenAI(**kwargs)
    
    @staticmethod
    def _create_openai(config: LLMConfig) -> BaseChatModel:
        """Create OpenAI instance - placeholder for future implementation"""
        raise ValueError("OpenAI provider is not yet implemented. Please select Azure OpenAI.")
    
    @staticmethod
    def _create_gemini(config: LLMConfig) -> BaseChatModel:
        """Create Gemini instance - placeholder for future implementation"""
        raise ValueError("Gemini provider is not yet implemented. Please select Azure OpenAI.")
    
    @staticmethod
    def _create_anthropic(config: LLMConfig) -> BaseChatModel:
        """Create Anthropic instance - placeholder for future implementation"""
        raise ValueError("Anthropic provider is not yet implemented. Please select Azure OpenAI.")

def get_default_config() -> Dict[str, Any]:
    """Get default configuration parameters"""
    return {
        "temperature": 0.7,
        "max_tokens": 4000,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }