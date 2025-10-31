"""Tests for prompt loader module"""

from pathlib import Path
from unittest.mock import patch


def test_prompt_loader_loads_yaml(tmp_path: Path) -> None:
    """Test that PromptLoader loads prompts from YAML"""
    from lib.prompts import PromptLoader

    # Create a test prompts.yaml
    yaml_content = """
simple:
  system: "Test system prompt"
  user: "Title: {title}\\nContent: {content}"

origami:
  system: "Test origami system"
  user: "Origami: {title}\\n{content}"
"""
    prompts_file = tmp_path / "prompts.yaml"
    prompts_file.write_text(yaml_content)

    # Change to tmp directory
    import os

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Force reload by clearing singleton
        PromptLoader._instance = None

        loader = PromptLoader()
        system, user = loader.get_simple_prompts()

        assert system == "Test system prompt"
        assert "{title}" in user
        assert "{content}" in user
    finally:
        os.chdir(original_dir)
        PromptLoader._instance = None


def test_prompt_loader_get_base_prompts() -> None:
    """Test getting base prompts"""
    from lib.prompts import PromptLoader

    # Force reload
    PromptLoader._instance = None

    loader = PromptLoader()
    system, user = loader.get_base_prompts()

    assert isinstance(system, str)
    assert isinstance(user, str)
    assert len(system) > 0
    assert len(user) > 0
    assert "{title}" in user
    assert "{content}" in user
    assert "{style}" in user
    assert "{style_description}" in user
    assert "{count}" in user


def test_prompt_loader_format_user_prompt() -> None:
    """Test formatting user prompt with variables"""
    from lib.prompts import PromptLoader

    loader = PromptLoader()
    template = "Title: {title}\\n\\nContent: {content}"
    result = loader.format_user_prompt(template, "Test Title", "Test Content")

    assert "Test Title" in result
    assert "Test Content" in result
    assert "{title}" not in result
    assert "{content}" not in result


def test_prompt_loader_singleton() -> None:
    """Test that PromptLoader is a singleton"""
    from lib.prompts import PromptLoader

    # Force reload
    PromptLoader._instance = None

    loader1 = PromptLoader()
    loader2 = PromptLoader()

    assert loader1 is loader2


def test_get_prompt_loader() -> None:
    """Test get_prompt_loader function"""
    from lib.prompts import get_prompt_loader

    loader = get_prompt_loader()

    assert loader is not None
    assert hasattr(loader, "get_base_prompts")
    assert hasattr(loader, "format_user_prompt")


def test_prompt_loader_fallback_when_no_file() -> None:
    """Test that fallback prompts are used when YAML file is missing"""
    from lib.prompts import PromptLoader

    # Force reload and ensure no prompts.yaml exists
    PromptLoader._instance = None

    with patch("pathlib.Path.exists", return_value=False):
        loader = PromptLoader()
        system, user = loader.get_base_prompts()

        # Should still return valid prompts (fallback)
        assert isinstance(system, str)
        assert isinstance(user, str)
        assert len(system) > 0
        assert len(user) > 0


def test_prompt_loader_prefers_local_yaml(tmp_path: Path) -> None:
    """Test that prompts.local.yaml takes precedence over prompts.yaml"""
    from lib.prompts import PromptLoader

    # Create both files
    default_yaml = """
simple:
  system: "Default system"
  user: "Default user"
"""
    local_yaml = """
simple:
  system: "Local system"
  user: "Local user"
"""

    (tmp_path / "prompts.yaml").write_text(default_yaml)
    (tmp_path / "prompts.local.yaml").write_text(local_yaml)

    import os

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        PromptLoader._instance = None

        loader = PromptLoader()
        system, user = loader.get_simple_prompts()

        # Should use local version
        assert system == "Local system"
        assert user == "Local user"
    finally:
        os.chdir(original_dir)
        PromptLoader._instance = None
