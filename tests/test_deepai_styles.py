"""Tests for DeepAI styles module"""

from unittest.mock import Mock, patch

from lib.deepai.styles import DeepAIStyle, DeepAIStyleLoader, get_style_loader


def test_deepai_style_dataclass() -> None:
    """Test DeepAIStyle dataclass"""
    style = DeepAIStyle(
        slug="test-style",
        name="Test Style",
        description="A test style for unit testing",
        endpoint="test-style",
        default_params={"param1": "value1"},
    )

    assert style.slug == "test-style"
    assert style.name == "Test Style"
    assert style.description == "A test style for unit testing"
    assert style.endpoint == "test-style"
    assert style.default_params == {"param1": "value1"}


def test_style_loader_singleton() -> None:
    """Test that get_style_loader returns the same instance"""
    loader1 = get_style_loader()
    loader2 = get_style_loader()

    assert loader1 is loader2


def test_style_loader_get_style() -> None:
    """Test getting a specific style"""
    loader = get_style_loader()
    style = loader.get_style("origami-3d-generator")

    assert style is not None
    assert style.slug == "origami-3d-generator"
    assert style.name == "3D Origami Generator"
    assert "origami" in style.description.lower() or "paper" in style.description.lower()
    assert style.endpoint == "origami-3d-generator"


def test_style_loader_get_nonexistent_style() -> None:
    """Test getting a style that doesn't exist"""
    loader = get_style_loader()
    style = loader.get_style("nonexistent-style-12345")

    assert style is None


def test_style_loader_list_styles() -> None:
    """Test listing all available styles"""
    loader = get_style_loader()
    styles = loader.list_styles()

    assert len(styles) > 0
    # Check that all items are DeepAIStyle instances
    assert all(isinstance(s, DeepAIStyle) for s in styles)
    # Check that styles are sorted by name
    names = [s.name for s in styles]
    assert names == sorted(names)


def test_style_loader_all_styles_have_descriptions() -> None:
    """Test that all styles have descriptions"""
    loader = get_style_loader()
    styles = loader.list_styles()

    for style in styles:
        assert style.description
        assert len(style.description) > 0
        assert isinstance(style.description, str)


def test_style_loader_common_styles_exist() -> None:
    """Test that common styles exist in the configuration"""
    loader = get_style_loader()

    # Test some common styles
    common_slugs = [
        "origami-3d-generator",
        "cyberpunk-generator",
        "watercolor-painting-generator",
        "pixel-art-generator",
    ]

    for slug in common_slugs:
        style = loader.get_style(slug)
        assert style is not None, f"Style {slug} should exist"
        assert style.slug == slug
        assert style.name
        assert style.description
        assert style.endpoint


@patch("lib.deepai.styles.Path.exists")
@patch("builtins.open")
def test_style_loader_fallback_on_missing_yaml(mock_open: Mock, mock_exists: Mock) -> None:
    """Test that loader uses fallback styles when YAML is missing"""
    mock_exists.return_value = False

    # Create a new loader instance (not using singleton)
    loader = DeepAIStyleLoader()

    # Should have fallback styles
    styles = loader.list_styles()
    assert len(styles) >= 2  # At least origami and text2img

    # Check that origami fallback exists
    origami = loader.get_style("origami-3d-generator")
    assert origami is not None
    assert origami.name == "3D Origami Generator"


def test_style_endpoint_format() -> None:
    """Test that all style endpoints are properly formatted"""
    loader = get_style_loader()
    styles = loader.list_styles()

    for style in styles:
        # Endpoint should not be a full URL
        assert not style.endpoint.startswith("http")
        # Endpoint should match slug for most cases
        assert isinstance(style.endpoint, str)
        assert len(style.endpoint) > 0
