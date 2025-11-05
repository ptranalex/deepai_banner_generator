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


@patch("lib.gpt.OpenAI")
def test_suggest_styles_returns_suggestions(mock_openai: Mock, mock_env_vars: None) -> None:
    """Test style suggestion with valid JSON response"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_response = Mock()
    # Mock GPT response with JSON suggestions
    json_response = """[
  {"slug": "cyberpunk-generator", "confidence": 0.92, "reasoning": "Technical content about AI"},
  {"slug": "hologram-3d-generator", "confidence": 0.85, "reasoning": "Future-focused theme"},
  {"slug": "neon-gradient-generator", "confidence": 0.78, "reasoning": "Modern aesthetic"}
]"""
    mock_response.choices = [Mock(message=Mock(content=json_response))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = GPTClient()
    available_styles = [
        ("cyberpunk-generator", "Cyberpunk Generator", "Neon-lit futuristic scenes"),
        ("hologram-3d-generator", "3D Hologram Generator", "Light-based forms"),
        ("neon-gradient-generator", "Neon Gradient Generator", "Vibrant neon colors"),
    ]

    suggestions = client.suggest_styles(
        title="AI Coding Tools",
        content="Article about modern AI development...",
        available_styles=available_styles,
        num_suggestions=3,
    )

    assert len(suggestions) == 3
    assert suggestions[0][0] == "cyberpunk-generator"
    assert suggestions[0][1] == 0.92
    assert "Technical" in suggestions[0][2]
    mock_client.chat.completions.create.assert_called_once()


@patch("lib.gpt.OpenAI")
def test_suggest_styles_handles_markdown_json(mock_openai: Mock, mock_env_vars: None) -> None:
    """Test style suggestion handles JSON wrapped in markdown code blocks"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_response = Mock()
    # GPT sometimes wraps JSON in code blocks
    markdown_json_response = """```json
[
  {"slug": "origami-3d-generator", "confidence": 0.88, "reasoning": "Paper-folded aesthetic"}
]
```"""
    mock_response.choices = [Mock(message=Mock(content=markdown_json_response))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = GPTClient()
    available_styles = [("origami-3d-generator", "3D Origami", "Paper-folded 3D compositions")]

    suggestions = client.suggest_styles(
        title="Test",
        content="Content",
        available_styles=available_styles,
    )

    assert len(suggestions) == 1
    assert suggestions[0][0] == "origami-3d-generator"
    assert suggestions[0][1] == 0.88


@patch("lib.gpt.OpenAI")
def test_suggest_styles_handles_invalid_json(mock_openai: Mock, mock_env_vars: None) -> None:
    """Test style suggestion returns empty list for invalid JSON"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_response = Mock()
    # Invalid JSON response
    mock_response.choices = [Mock(message=Mock(content="Not valid JSON at all"))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = GPTClient()
    available_styles = [("test-style", "Test Style", "Test description")]

    suggestions = client.suggest_styles(
        title="Test",
        content="Content",
        available_styles=available_styles,
    )

    # Should return empty list gracefully instead of crashing
    assert suggestions == []


@patch("lib.gpt.OpenAI")
def test_suggest_styles_handles_api_exception(mock_openai: Mock, mock_env_vars: None) -> None:
    """Test style suggestion handles API exceptions gracefully"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    mock_openai.return_value = mock_client

    client = GPTClient()
    available_styles = [("test-style", "Test Style", "Test description")]

    # Should return empty list instead of raising exception
    suggestions = client.suggest_styles(
        title="Test",
        content="Content",
        available_styles=available_styles,
    )

    assert suggestions == []


@patch("lib.gpt.OpenAI")
def test_suggest_styles_sorts_by_confidence(mock_openai: Mock, mock_env_vars: None) -> None:
    """Test style suggestions are sorted by confidence descending"""
    from lib.gpt import GPTClient

    mock_client = Mock()
    mock_response = Mock()
    # Unsorted confidence scores
    json_response = """[
  {"slug": "style-a", "confidence": 0.75, "reasoning": "Reason A"},
  {"slug": "style-b", "confidence": 0.92, "reasoning": "Reason B"},
  {"slug": "style-c", "confidence": 0.83, "reasoning": "Reason C"}
]"""
    mock_response.choices = [Mock(message=Mock(content=json_response))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = GPTClient()
    available_styles = [
        ("style-a", "Style A", "Description A"),
        ("style-b", "Style B", "Description B"),
        ("style-c", "Style C", "Description C"),
    ]

    suggestions = client.suggest_styles(
        title="Test",
        content="Content",
        available_styles=available_styles,
    )

    # Should be sorted by confidence (highest first)
    assert suggestions[0][0] == "style-b"  # 0.92
    assert suggestions[1][0] == "style-c"  # 0.83
    assert suggestions[2][0] == "style-a"  # 0.75
    assert suggestions[0][1] > suggestions[1][1] > suggestions[2][1]
