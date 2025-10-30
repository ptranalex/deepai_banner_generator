"""Tests for GPT client module"""

import pytest
from unittest.mock import Mock, patch


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
def test_generate_simple_prompt(mock_openai: Mock, mock_env_vars: None) -> None:
    """Test simple prompt generation"""
    from lib.gpt import GPTClient

    # Mock the OpenAI response
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test banner prompt"))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = GPTClient()
    prompt = client.generate_simple_prompt("Test Title", "Test content here")

    assert prompt == "Test banner prompt"
    mock_client.chat.completions.create.assert_called_once()


@patch("lib.gpt.OpenAI")
def test_generate_simple_prompt_removes_quotes(
    mock_openai: Mock, mock_env_vars: None
) -> None:
    """Test that simple prompt generation removes surrounding quotes"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content='"Quoted prompt"'))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = GPTClient()
    prompt = client.generate_simple_prompt("Title", "Content")

    assert prompt == "Quoted prompt"
    assert not prompt.startswith('"')


@patch("lib.gpt.OpenAI")
def test_generate_origami_prompts(mock_openai: Mock, mock_env_vars: None) -> None:
    """Test origami prompt generation returns 10 prompts"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_response = Mock()
    numbered_prompts = "\n".join([f"{i}. Prompt {i}" for i in range(1, 11)])
    mock_response.choices = [Mock(message=Mock(content=numbered_prompts))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = GPTClient()
    prompts = client.generate_origami_prompts("Test Title", "Test content")

    assert len(prompts) == 10
    assert all(isinstance(p, str) for p in prompts)
    assert prompts[0] == "Prompt 1"


@patch("lib.gpt.OpenAI")
def test_generate_origami_prompts_handles_various_formats(
    mock_openai: Mock, mock_env_vars: None
) -> None:
    """Test origami prompts handle different numbering formats"""
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
7. Seventh prompt
8. Eighth prompt
9. Ninth prompt
10. Tenth prompt"""
    mock_response.choices = [Mock(message=Mock(content=mixed_format))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = GPTClient()
    prompts = client.generate_origami_prompts("Title", "Content")

    assert len(prompts) == 10
    assert prompts[0] == "First prompt"
    assert prompts[1] == "Second prompt"
    assert prompts[2] == "Third prompt"


@patch("lib.gpt.OpenAI")
def test_generate_simple_prompt_handles_exception(
    mock_openai: Mock, mock_env_vars: None
) -> None:
    """Test simple prompt generation handles API exceptions"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    mock_openai.return_value = mock_client

    client = GPTClient()

    with pytest.raises(SystemExit):
        client.generate_simple_prompt("Title", "Content")


@patch("lib.gpt.OpenAI")
def test_generate_origami_prompts_handles_exception(
    mock_openai: Mock, mock_env_vars: None
) -> None:
    """Test origami prompt generation handles API exceptions"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    mock_openai.return_value = mock_client

    client = GPTClient()

    with pytest.raises(SystemExit):
        client.generate_origami_prompts("Title", "Content")
