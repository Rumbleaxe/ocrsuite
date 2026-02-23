"""Tests for Ollama client."""

from ocrsuite.config import OllamaConfig
from ocrsuite.ollama_client import OllamaClient


def test_ollama_client_init():
    """Test Ollama client initialization."""
    config = OllamaConfig(url="http://localhost:11434", model="llama2-vision")
    client = OllamaClient(config)
    assert client.url == "http://localhost:11434"
    assert client.model == "llama2-vision"
    assert client.timeout == 300


def test_ollama_client_url_trailing_slash():
    """Test that trailing slash is removed from URL."""
    config = OllamaConfig(url="http://localhost:11434/")
    client = OllamaClient(config)
    assert client.url == "http://localhost:11434"


def test_health_check_failure():
    """Test health check with unreachable server."""
    config = OllamaConfig(url="http://localhost:99999")  # Unlikely port
    client = OllamaClient(config)
    assert not client.health_check()
