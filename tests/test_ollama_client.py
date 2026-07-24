"""Tests for Ollama client."""

import base64

import pytest

from ocrsuite.config import OllamaConfig
from ocrsuite.ollama_client import OllamaClient
from ocrsuite.utils import OllamaError


def test_ollama_client_init():
    config = OllamaConfig(url="http://localhost:11434", model="llama2-vision")
    client = OllamaClient(config)
    assert client.url == "http://localhost:11434"
    assert client.model == "llama2-vision"
    assert client.timeout == 600


def test_ollama_client_url_trailing_slash():
    config = OllamaConfig(url="http://localhost:11434/")
    client = OllamaClient(config)
    assert client.url == "http://localhost:11434"


def test_health_check_failure():
    config = OllamaConfig(url="http://localhost:99999")
    client = OllamaClient(config)
    assert not client.health_check()


def test_encode_image(sample_image):
    encoded = OllamaClient._encode_image(sample_image)
    assert isinstance(encoded, str)
    decoded = base64.b64decode(encoded)
    original = sample_image.read_bytes()
    assert decoded == original


def test_ocr_image_mocked(sample_image, mocker):
    mock_post = mocker.patch("requests.post")
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"response": "Extracted text from page."}

    config = OllamaConfig(url="http://localhost:11434", model="ocrsuite-deepseek")
    client = OllamaClient(config)
    result = client.ocr_image(sample_image)

    assert result == "Extracted text from page."


def test_ocr_image_default_prompt(sample_image, mocker):
    """Verify the default prompt uses DeepSeek-OCR command syntax."""
    mock_post = mocker.patch("requests.post")
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"response": "OK"}

    config = OllamaConfig(url="http://localhost:11434", model="ocrsuite-deepseek")
    client = OllamaClient(config)
    client.ocr_image(sample_image)

    call_data = mock_post.call_args.kwargs["json"]
    assert call_data["prompt"] == "Free OCR."


def test_retry_exhaustion(sample_image, mocker):
    mock_post = mocker.patch("requests.post")
    from requests.exceptions import ConnectionError as ReqConnectionError

    mock_post.side_effect = ReqConnectionError("Connection refused")

    config = OllamaConfig(url="http://localhost:11434", model="ocrsuite-deepseek", max_retries=2)
    client = OllamaClient(config)

    with pytest.raises(OllamaError, match="Could not connect"):
        client.ocr_image(sample_image)

    assert mock_post.call_count == 3  # initial + 2 retries


def test_generate_text(mocker):
    mock_post = mocker.patch("requests.post")
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"response": "Generated text response."}

    config = OllamaConfig(url="http://localhost:11434", model="llava:13b")
    client = OllamaClient(config)
    result = client.generate_text("Hello")

    assert result == "Generated text response."
    call_data = mock_post.call_args.kwargs["json"]
    assert "images" not in call_data  # text-only, no images field
