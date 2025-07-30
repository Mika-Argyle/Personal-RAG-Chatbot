"""
Configuration management for RAG Chatbot API.

This module handles all environment variables, API settings, 
and application configuration.

It uses Pydantic for validation and type safety.
    
    Mika Argyle - Jul 22 2025

"""

import os
from typing import Optional
from pydantic import BaseSettings, field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    Environment variables should match the field names (case insensitive).
    """
    
    # ===== OpenAI Configuration =====
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_model_fallback: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # ===== Pinecone Configuration =====
    pinecone_api_key: str
    pinecone_index_name: str = "portfolio-rag"
    pinecone_environment: Optional[str] = None  # Not needed for newer Pinecone versions
    
    # ===== API Configuration =====
    max_tokens: int = 500
    temperature: float = 0.7
    embedding_dimension: int = 1536  # text-embedding-3-small dimension
    
    # ===== RAG Configuration =====
    rag_top_k: int = 5  # Number of similar documents to retrieve
    rag_min_score: float = 0.7  # Minimum similarity score threshold
    chunk_size: int = 1000  # Document chunking size
    chunk_overlap: int = 200  # Overlap between chunks
    
    # ===== Application Configuration =====
    environment: str = "development"
    debug: bool = True
    api_title: str = "RAG Chatbot API"
    api_version: str = "1.0.0"
    api_description: str = "Personal portfolio chatbot with RAG capabilities"
    
    # ===== CORS Configuration =====
    cors_origins: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    @field_validator('openai_api_key')
    @classmethod
    def validate_openai_key(cls, v):
        """Validate OpenAI API key format."""
        if not v or not v.startswith('sk-'):
            raise ValueError('OpenAI API key must start with "sk-"')
        return v
    
    @field_validator('pinecone_api_key')
    @classmethod
    def validate_pinecone_key(cls, v):
        """Validate Pinecone API key is present."""
        if not v or len(v) < 10:
            raise ValueError('Pinecone API key must be provided and valid')
        return v
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v):
        """Validate temperature is between 0 and 2."""
        if not 0 <= v <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v
    
    @field_validator('rag_min_score')
    @classmethod
    def validate_min_score(cls, v):
        """Validate minimum score is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('Minimum score must be between 0 and 1')
        return v
    
    @field_validator('cors_origins')
    @classmethod
    def validate_cors_origins(cls, v):
        """Ensure CORS origins is a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def get_openai_config(self) -> dict:
        """Get OpenAI configuration dictionary."""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "fallback_model": self.openai_model_fallback,
            "embedding_model": self.openai_embedding_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
    
    def get_pinecone_config(self) -> dict:
        """Get Pinecone configuration dictionary."""
        return {
            "api_key": self.pinecone_api_key,
            "index_name": self.pinecone_index_name,
            "environment": self.pinecone_environment,
            "dimension": self.embedding_dimension
        }
    
    def get_rag_config(self) -> dict:
        """Get RAG configuration dictionary."""
        return {
            "top_k": self.rag_top_k,
            "min_score": self.rag_min_score,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        # Define environment variable names explicitly if different from field names
        fields = {
            'cors_origins': {
                'env': 'CORS_ORIGINS'
            }
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures we only create the settings object once
    and reuse it throughout the application lifecycle.
    
    Returns:
        Settings: Cached settings instance
    """
    return Settings()


# For easy importing in other modules
settings = get_settings()


# ===== Configuration Validation Function =====
def validate_configuration() -> bool:
    """
    Validate that all required configuration is present and valid.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    
    Raises:
        ValueError: If critical configuration is missing or invalid
    """
    try:
        # This will trigger validation
        config = get_settings()
        
        # Additional runtime checks
        required_env_vars = [
            'OPENAI_API_KEY',
            'PINECONE_API_KEY'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
        
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False


# ===== Development Helper Functions =====
def print_config_summary():
    """Print a summary of current configuration (without sensitive data)."""
    config = get_settings()
    
    print("🔧 RAG Chatbot Configuration Summary")
    print("=" * 40)
    print(f"Environment: {config.environment}")
    print(f"Debug Mode: {config.debug}")
    print(f"API Title: {config.api_title}")
    print(f"OpenAI Model: {config.openai_model}")
    print(f"Embedding Model: {config.openai_embedding_model}")
    print(f"Pinecone Index: {config.pinecone_index_name}")
    print(f"RAG Top-K: {config.rag_top_k}")
    print(f"Min Score: {config.rag_min_score}")
    print(f"CORS Origins: {config.cors_origins}")
    print("=" * 40)


if __name__ == "__main__":
    """Run configuration validation and print summary when executed directly."""
    if validate_configuration():
        print("✅ Configuration is valid!")
        print_config_summary()
    else:
        print("❌ Configuration validation failed!")
        exit(1)
