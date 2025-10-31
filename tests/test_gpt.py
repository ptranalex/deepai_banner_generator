"""Tests for GPT client module"""

from unittest.mock import Mock, patch

import pytest


def test_gpt_client_initialization(mock_env_vars: None) -> None:
    """Test GPT client initialization"""
    from lib.gpt import GPTClient

    client = GPTClient()

    assert client.api_key.startswith("sk-test")
    assert client.model == "gpt-4o"
    assert client.temperature == 0.9


def test_gpt_client_custom_api_key() -> None:
    """Test GPT client with custom API key"""
    from lib.gpt import GPTClient

    custom_key = "sk-custom" + "x" * 40
    client = GPTClient(api_key=custom_key)

    assert client.api_key == custom_key


@patch("lib.gpt.OpenAI")
def test_generate_prompts_default(mock_openai: Mock, mock_env_vars: None) -> None:
    """Test prompt generation with default parameters (10 prompts)"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_response = Mock()
    numbered_prompts = "\n".join([f"{i}. Prompt {i}" for i in range(1, 11)])
    mock_response.choices = [Mock(message=Mock(content=numbered_prompts))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = GPTClient()
    prompts = client.generate_prompts("Test Title", "Test content", "origami-3d-generator")

    assert len(prompts) == 10
    assert all(isinstance(p, str) for p in prompts)
    assert prompts[0] == "Prompt 1"
    mock_client.chat.completions.create.assert_called_once()


@patch("lib.gpt.OpenAI")
def test_generate_prompts_custom_count(mock_openai: Mock, mock_env_vars: None) -> None:
    """Test prompt generation with custom count"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_response = Mock()
    numbered_prompts = "\n".join([f"{i}. Prompt {i}" for i in range(1, 6)])
    mock_response.choices = [Mock(message=Mock(content=numbered_prompts))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = GPTClient()
    prompts = client.generate_prompts(
        "Test Title", "Test content", "cyberpunk-generator", num_prompts=5
    )

    assert len(prompts) == 5
    assert prompts[0] == "Prompt 1"
    assert prompts[4] == "Prompt 5"


@patch("lib.gpt.OpenAI")
def test_generate_prompts_handles_various_formats(mock_openai: Mock, mock_env_vars: None) -> None:
    """Test prompts handle different numbering formats"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_response = Mock()
    # Mix of formats: "1.", "2)", "3 -", "4-"
    mixed_format = """1. First prompt
2) Second prompt
3 - Third prompt
4- Fourth prompt
5. Fifth prompt
6. Sixth prompt
7. Seventh prompt"""
    mock_response.choices = [Mock(message=Mock(content=mixed_format))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = GPTClient()
    prompts = client.generate_prompts(
        "Title", "Content", "watercolor-painting-generator", num_prompts=7
    )

    assert len(prompts) == 7
    assert prompts[0] == "First prompt"
    assert prompts[1] == "Second prompt"
    assert prompts[2] == "Third prompt"


@patch("lib.gpt.OpenAI")
def test_generate_prompts_handles_exception(mock_openai: Mock, mock_env_vars: None) -> None:
    """Test prompt generation handles API exceptions"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    mock_openai.return_value = mock_client

    client = GPTClient()

    with pytest.raises(SystemExit):
        client.generate_prompts("Title", "Content", "origami-3d-generator")
