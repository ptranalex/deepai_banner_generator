"""Pytest fixtures and configuration"""

import pytest
from pathlib import Path


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock environment variables for testing"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test" + "x" * 40)
    monkeypatch.setenv("DEEPAI_API_KEY", "test-deepai" + "x" * 20)


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Temporary output directory"""
    output_dir = tmp_path / "banners"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def temp_input_dir(tmp_path: Path) -> Path:
    """Temporary input directory with sample markdown"""
    input_dir = tmp_path / "posts"
    input_dir.mkdir()

    # Create a sample markdown file
    sample_md = input_dir / "test-post.md"
    sample_md.write_text(
        """---
title: "Test Post"
date: 2025-01-01
tags: [test, example]
---

# Test Heading

This is a test blog post content.
"""
    )

    return input_dir
