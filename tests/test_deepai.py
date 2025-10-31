"""Tests for DeepAI client module"""

from pathlib import Path
from unittest.mock import Mock, patch


def test_deepai_client_initialization(mock_env_vars: None) -> None:
    """Test DeepAI client initialization"""
    from lib.deepai import DeepAIClient

    client = DeepAIClient()

    assert client.api_key.startswith("test-deepai")
    assert client.base_api_url == "https://api.deepai.org/api"
    assert client.timeout == 60


def test_deepai_client_custom_api_key() -> None:
    """Test DeepAI client with custom API key"""
    from lib.deepai import DeepAIClient

    custom_key = "custom-deepai-key-12345678901234"
    client = DeepAIClient(api_key=custom_key)

    assert client.api_key == custom_key


@patch("lib.deepai.client.requests.post")
def test_generate_image_success(mock_post: Mock, mock_env_vars: None) -> None:
    """Test successful image generation with default style"""
    from lib.deepai import DeepAIClient

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"output_url": "https://example.com/image.jpg"}
    mock_post.return_value = mock_response

    client = DeepAIClient()
    url = client.generate_image(
        "test prompt", deepai_style="origami-3d-generator", width=1792, height=1024
    )

    assert url == "https://example.com/image.jpg"
    mock_post.assert_called_once()

    # Verify API call parameters
    call_args = mock_post.call_args
    assert call_args[1]["data"]["text"] == "test prompt"
    assert call_args[1]["data"]["width"] == "1792"
    assert call_args[1]["data"]["height"] == "1024"
    # Check URL includes the style endpoint
    assert "origami-3d-generator" in call_args[0][0]


@patch("lib.deepai.client.requests.post")
def test_generate_image_api_error(mock_post: Mock, mock_env_vars: None) -> None:
    """Test image generation with API error"""
    from lib.deepai import DeepAIClient

    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_post.return_value = mock_response

    client = DeepAIClient()
    url = client.generate_image("test prompt")

    assert url is None


@patch("lib.deepai.client.requests.get")
def test_download_image_success(mock_get: Mock, mock_env_vars: None, tmp_path: Path) -> None:
    """Test successful image download"""
    from lib.deepai import DeepAIClient

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"fake image data"
    mock_get.return_value = mock_response

    client = DeepAIClient()
    output_path = tmp_path / "test.png"

    result = client.download_image("https://example.com/image.jpg", output_path)

    assert result is True
    assert output_path.exists()
    assert output_path.read_bytes() == b"fake image data"


@patch("lib.deepai.client.requests.get")
def test_download_image_failure(mock_get: Mock, mock_env_vars: None, tmp_path: Path) -> None:
    """Test image download failure"""
    from lib.deepai import DeepAIClient

    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    client = DeepAIClient()
    output_path = tmp_path / "test.png"

    result = client.download_image("https://example.com/image.jpg", output_path)

    assert result is False
    assert not output_path.exists()


@patch("lib.deepai.DeepAIClient.download_image")
@patch("lib.deepai.DeepAIClient.generate_image")
def test_generate_and_save_success(
    mock_generate: Mock, mock_download: Mock, mock_env_vars: None, tmp_path: Path
) -> None:
    """Test generate_and_save combines both operations"""
    from lib.deepai import DeepAIClient

    mock_generate.return_value = "https://example.com/generated.jpg"
    mock_download.return_value = True

    client = DeepAIClient()
    output_path = tmp_path / "banner.png"

    result = client.generate_and_save(
        "test prompt", output_path, deepai_style="origami-3d-generator"
    )

    assert result is True
    # Updated to match new default resolution and deepai_style parameter
    mock_generate.assert_called_once_with(
        "test prompt", "origami-3d-generator", 1792, 1024, "standard"
    )
    mock_download.assert_called_once_with("https://example.com/generated.jpg", output_path)


@patch("lib.deepai.DeepAIClient.generate_image")
def test_generate_and_save_generation_fails(
    mock_generate: Mock, mock_env_vars: None, tmp_path: Path
) -> None:
    """Test generate_and_save when generation fails"""
    from lib.deepai import DeepAIClient

    mock_generate.return_value = None

    client = DeepAIClient()
    output_path = tmp_path / "banner.png"

    result = client.generate_and_save(
        "test prompt", output_path, deepai_style="origami-3d-generator"
    )

    assert result is False
