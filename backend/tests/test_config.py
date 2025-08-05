"""
Tests for configuration management and Pydantic validators.

Tests all field validators, environment variable loading,
and configuration utility methods.
"""

import os
import pytest
from pydantic import ValidationError
from unittest.mock import patch
from app.config import Settings, get_settings, validate_configuration


class TestSettingsValidators:
    """Test all Pydantic field validators."""

    @pytest.mark.unit
    def test_openai_api_key_valid(self):
        """Test OpenAI API key validation with valid key."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': 'test-pinecone-key'
        }):
            settings = Settings()
            assert settings.openai_api_key == 'sk-test123456789'

    @pytest.mark.unit
    def test_openai_api_key_invalid_format(self):
        """Test OpenAI API key validation with invalid format."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'invalid-key-format',
            'PINECONE_API_KEY': 'test-pinecone-key'
        }):
            with pytest.raises(ValidationError, 
                               match='OpenAI API key must start with "sk-"'):
                Settings()

    @pytest.mark.unit
    def test_openai_api_key_empty(self):
        """Test OpenAI API key validation with empty key."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': '',
            'PINECONE_API_KEY': 'test-pinecone-key'
        }):
            with pytest.raises(ValidationError, 
                               match='OpenAI API key must start with "sk-"'):
                Settings()

    @pytest.mark.unit
    def test_pinecone_api_key_valid(self):
        """Test Pinecone API key validation with valid key."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': 'test-pinecone-key-12345'
        }):
            settings = Settings()
            assert settings.pinecone_api_key == 'test-pinecone-key-12345'

    @pytest.mark.unit
    def test_pinecone_api_key_too_short(self):
        """Test Pinecone API key validation with too short key."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': 'short'
        }):
            with pytest.raises(ValidationError, 
                               match='Pinecone API key must be ' \
                               'provided and valid'):
                Settings()

    @pytest.mark.unit
    def test_pinecone_api_key_empty(self):
        """Test Pinecone API key validation with empty key."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': ''
        }):
            with pytest.raises(ValidationError, 
                               match='Pinecone API key must be ' \
                               'provided and valid'):
                Settings()

    @pytest.mark.unit
    def test_temperature_valid_range(self):
        """Test temperature validation with valid values."""
        valid_temps = [0.0, 0.5, 1.0, 1.5, 2.0]
        
        for temp in valid_temps:
            with patch.dict(os.environ, {
                'OPENAI_API_KEY': 'sk-test123456789',
                'PINECONE_API_KEY': 'test-pinecone-key',
                'TEMPERATURE': str(temp)
            }):
                settings = Settings()
                assert settings.temperature == temp

    @pytest.mark.unit
    def test_temperature_invalid_range(self):
        """Test temperature validation with invalid values."""
        invalid_temps = [-0.1, 2.1, 5.0]
        
        for temp in invalid_temps:
            with patch.dict(os.environ, {
                'OPENAI_API_KEY': 'sk-test123456789',
                'PINECONE_API_KEY': 'test-pinecone-key',
                'TEMPERATURE': str(temp)
            }):
                with pytest.raises(ValidationError, 
                                   match='Temperature must be ' \
                                   'between 0 and 2'):
                    Settings()

    @pytest.mark.unit
    def test_rag_min_score_valid_range(self):
        """Test RAG minimum score validation with valid values."""
        valid_scores = [0.0, 0.3, 0.5, 0.7, 1.0]
        
        for score in valid_scores:
            with patch.dict(os.environ, {
                'OPENAI_API_KEY': 'sk-test123456789',
                'PINECONE_API_KEY': 'test-pinecone-key',
                'RAG_MIN_SCORE': str(score)
            }):
                settings = Settings()
                assert settings.rag_min_score == score

    @pytest.mark.unit
    def test_rag_min_score_invalid_range(self):
        """Test RAG minimum score validation with invalid values."""
        invalid_scores = [-0.1, 1.1, 2.0]
        
        for score in invalid_scores:
            with patch.dict(os.environ, {
                'OPENAI_API_KEY': 'sk-test123456789',
                'PINECONE_API_KEY': 'test-pinecone-key',
                'RAG_MIN_SCORE': str(score)
            }):
                with pytest.raises(ValidationError, 
                                   match='Minimum score must be ' \
                                   'between 0 and 1'):
                    Settings()



class TestSettingsDefaults:
    """Test default values and configuration."""

    @pytest.mark.unit
    def test_default_values(self):
        """Test that default values are set correctly."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': 'test-pinecone-key'
        }):
            settings = Settings()
            
            # OpenAI defaults
            assert settings.openai_model == "gpt-4o-mini"
            assert settings.openai_model_fallback == "gpt-4o"
            assert settings.openai_embedding_model == "text-embedding-3-small"
            
            # Pinecone defaults
            assert settings.pinecone_index_name == "portfolio-rag"
            
            # API defaults
            assert settings.max_tokens == 500
            assert settings.temperature == 0.7
            assert settings.embedding_dimension == 1536
            
            # RAG defaults
            assert settings.rag_top_k == 5
            assert settings.rag_min_score == 0.7
            assert settings.chunk_size == 1000
            assert settings.chunk_overlap == 200
            
            # App defaults
            assert settings.environment == "development"
            assert settings.debug is True
            assert settings.api_title == "RAG Chatbot API"


class TestSettingsProperties:
    """Test Settings property methods."""

    @pytest.mark.unit
    def test_is_production_true(self):
        """Test is_production property returns True for production."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': 'test-pinecone-key',
            'ENVIRONMENT': 'production'
        }):
            settings = Settings()
            assert settings.is_production is True
            assert settings.is_development is False

    @pytest.mark.unit
    def test_is_development_true(self):
        """Test is_development property returns True for development."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': 'test-pinecone-key',
            'ENVIRONMENT': 'development'
        }):
            settings = Settings()
            assert settings.is_development is True
            assert settings.is_production is False

    @pytest.mark.unit
    def test_get_openai_config(self):
        """Test OpenAI configuration dictionary."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': 'test-pinecone-key'
        }):
            settings = Settings()
            config = settings.get_openai_config()
            
            assert config["api_key"] == "sk-test123456789"
            assert config["model"] == "gpt-4o-mini"
            assert config["fallback_model"] == "gpt-4o"
            assert config["embedding_model"] == "text-embedding-3-small"
            assert config["max_tokens"] == 500
            assert config["temperature"] == 0.7

    @pytest.mark.unit
    def test_get_pinecone_config(self):
        """Test Pinecone configuration dictionary."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': 'test-pinecone-key'
        }):
            settings = Settings()
            config = settings.get_pinecone_config()
            
            assert config["api_key"] == "test-pinecone-key"
            assert config["index_name"] == "portfolio-rag"
            assert config["dimension"] == 1536

    @pytest.mark.unit
    def test_get_rag_config(self):
        """Test RAG configuration dictionary."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': 'test-pinecone-key'
        }):
            settings = Settings()
            config = settings.get_rag_config()
            
            assert config["top_k"] == 5
            assert config["min_score"] == 0.7
            assert config["chunk_size"] == 1000
            assert config["chunk_overlap"] == 200


class TestConfigurationUtilities:
    """Test configuration utility functions."""

    @pytest.mark.unit
    def test_get_settings_caching(self):
        """Test that get_settings returns cached instance."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': 'test-pinecone-key'
        }):
            settings1 = get_settings()
            settings2 = get_settings()
            
            # Should be the same instance due to lru_cache
            assert settings1 is settings2

    @pytest.mark.unit
    def test_validate_configuration_success(self):
        """Test configuration validation with valid environment."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789',
            'PINECONE_API_KEY': 'test-pinecone-key'
        }):
            assert validate_configuration() is True

    @pytest.mark.unit
    def test_validate_configuration_missing_openai_key(self):
        """Test configuration validation with missing OpenAI key."""
        with patch.dict(os.environ, {
            'PINECONE_API_KEY': 'test-pinecone-key'
        }, clear=True):
            assert validate_configuration() is False

    @pytest.mark.unit
    def test_validate_configuration_missing_pinecone_key(self):
        """Test configuration validation with missing Pinecone key."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123456789'
        }, clear=True):
            assert validate_configuration() is False