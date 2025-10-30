"""Tests for configuration module"""

import pytest
from pydantic import ValidationError
from pathlib import Path


def test_settings_loads_from_env(mock_env_vars: None) -> None:
    """Test that settings load from environment variables"""
    from lib.config import Settings

    settings = Settings()  # type: ignore[call-arg]
    assert settings.openai_api_key.startswith("sk-test")
    assert settings.deepai_api_key.startswith("test-deepai")


def test_settings_validates_api_key_length(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that API keys must meet minimum length"""
    monkeypatch.setenv("OPENAI_API_KEY", "short")
    monkeypatch.setenv("DEEPAI_API_KEY", "short")

    from lib.config import Settings

    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


def test_settings_default_values(mock_env_vars: None) -> None:
    """Test default configuration values"""
    from lib.config import Settings

    settings = Settings()  # type: ignore[call-arg]
    assert settings.openai_model == "gpt-4o"
    assert settings.openai_temperature == 0.9
    assert settings.default_width == 1024
    assert settings.default_height == 512
    assert settings.default_style == "origami"


def test_settings_validates_dimensions_multiple_of_32(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that dimensions must be multiples of 32"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test" + "x" * 40)
    monkeypatch.setenv("DEEPAI_API_KEY", "test-deepai" + "x" * 20)
    monkeypatch.setenv("DEFAULT_WIDTH", "1000")  # Not multiple of 32

    from lib.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings()  # type: ignore[call-arg]
    assert "Must be multiple of 32" in str(exc_info.value)


def test_settings_validates_dimension_range(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that dimensions must be within valid range"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test" + "x" * 40)
    monkeypatch.setenv("DEEPAI_API_KEY", "test-deepai" + "x" * 20)
    monkeypatch.setenv("DEFAULT_WIDTH", "2000")  # Too large

    from lib.config import Settings

    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


def test_get_settings_singleton(mock_env_vars: None) -> None:
    """Test that get_settings returns same instance"""
    from lib.config import get_settings

    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_settings_temperature_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test temperature must be between 0 and 2"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test" + "x" * 40)
    monkeypatch.setenv("DEEPAI_API_KEY", "test-deepai" + "x" * 20)
    monkeypatch.setenv("OPENAI_TEMPERATURE", "3.0")  # Too high

    from lib.config import Settings

    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]
