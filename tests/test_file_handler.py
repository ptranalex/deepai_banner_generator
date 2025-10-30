"""Tests for file handler module"""

import pytest
from pathlib import Path


def test_find_markdown_files(temp_input_dir: Path) -> None:
    """Test finding markdown files in directory"""
    from lib.file_handler import MarkdownHandler

    # Create additional markdown files
    (temp_input_dir / "post1.md").write_text("# Post 1")
    (temp_input_dir / "post2.md").write_text("# Post 2")
    (temp_input_dir / "not-markdown.txt").write_text("Not markdown")

    files = MarkdownHandler.find_markdown_files(temp_input_dir)

    assert len(files) == 3  # test-post.md + post1.md + post2.md
    assert all(f.suffix == ".md" for f in files)
    assert all(f.exists() for f in files)


def test_find_markdown_files_empty_directory(tmp_path: Path) -> None:
    """Test finding markdown files in empty directory"""
    from lib.file_handler import MarkdownHandler

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    files = MarkdownHandler.find_markdown_files(empty_dir)

    assert files == []


def test_parse_markdown_with_frontmatter(temp_input_dir: Path) -> None:
    """Test parsing markdown with YAML frontmatter"""
    from lib.file_handler import MarkdownHandler

    md_file = temp_input_dir / "with-frontmatter.md"
    md_file.write_text(
        """---
title: "Test Title"
date: 2025-01-01
tags: [python, testing]
---

# Main Heading

This is the body content.
"""
    )

    front_matter, body = MarkdownHandler.parse_markdown_post(md_file)

    assert front_matter["title"] == "Test Title"
    # YAML parses dates as datetime.date objects
    assert str(front_matter["date"]) == "2025-01-01"
    assert front_matter["tags"] == ["python", "testing"]
    assert "Main Heading" in body
    assert "body content" in body


def test_parse_markdown_without_frontmatter(tmp_path: Path) -> None:
    """Test parsing markdown without frontmatter"""
    from lib.file_handler import MarkdownHandler

    md_file = tmp_path / "no-frontmatter.md"
    md_file.write_text(
        """# Just a Heading

Some content without frontmatter.
"""
    )

    front_matter, body = MarkdownHandler.parse_markdown_post(md_file)

    assert front_matter == {}
    assert "Just a Heading" in body
    assert "without frontmatter" in body


def test_generate_output_path() -> None:
    """Test generating output path from input file"""
    from lib.file_handler import OutputHandler

    input_file = Path("/input/my-post.md")
    output_dir = Path("/output")

    result = OutputHandler.generate_output_path(input_file, output_dir)

    assert result == Path("/output/my-post_banner.png")


def test_generate_output_path_custom_suffix() -> None:
    """Test generating output path with custom suffix"""
    from lib.file_handler import OutputHandler

    input_file = Path("/input/article.md")
    output_dir = Path("/images")

    result = OutputHandler.generate_output_path(input_file, output_dir, suffix="_cover")

    assert result == Path("/images/article_cover.png")


def test_ensure_output_directory_creates_dirs(tmp_path: Path) -> None:
    """Test that ensure_output_directory creates nested directories"""
    from lib.file_handler import OutputHandler

    output_path = tmp_path / "nested" / "dirs" / "output.png"

    OutputHandler.ensure_output_directory(output_path)

    assert output_path.parent.exists()
    assert output_path.parent.is_dir()


def test_ensure_output_directory_idempotent(tmp_path: Path) -> None:
    """Test that ensure_output_directory is idempotent"""
    from lib.file_handler import OutputHandler

    output_path = tmp_path / "existing" / "output.png"
    output_path.parent.mkdir(parents=True)

    # Should not raise error
    OutputHandler.ensure_output_directory(output_path)

    assert output_path.parent.exists()


def test_generate_batch_output_paths() -> None:
    """Test batch path generation with timestamp"""
    from lib.file_handler import OutputHandler

    input_file = Path("my-post.md")
    output_dir = Path("/output")
    count = 3
    timestamp = "20251030_143022"

    paths = OutputHandler.generate_batch_output_paths(
        input_file, output_dir, count, timestamp
    )

    assert len(paths) == 3
    assert paths[0] == Path("/output/my-post_banner_20251030_143022_01.png")
    assert paths[1] == Path("/output/my-post_banner_20251030_143022_02.png")
    assert paths[2] == Path("/output/my-post_banner_20251030_143022_03.png")


def test_generate_batch_output_paths_auto_timestamp() -> None:
    """Test batch path generation with auto timestamp"""
    from lib.file_handler import OutputHandler

    input_file = Path("test.md")
    output_dir = Path("/out")
    count = 2

    paths = OutputHandler.generate_batch_output_paths(input_file, output_dir, count)

    assert len(paths) == 2
    assert all(p.parent == output_dir for p in paths)
    assert all(p.stem.startswith("test_banner_") for p in paths)
    assert paths[0].name.endswith("_01.png")
    assert paths[1].name.endswith("_02.png")


def test_generate_batch_output_paths_large_count() -> None:
    """Test batch path generation with large count"""
    from lib.file_handler import OutputHandler

    input_file = Path("article.md")
    output_dir = Path("/banners")
    count = 10
    timestamp = "20251030_120000"

    paths = OutputHandler.generate_batch_output_paths(
        input_file, output_dir, count, timestamp
    )

    assert len(paths) == 10
    # Check sequential numbering with zero padding
    assert paths[0].name == "article_banner_20251030_120000_01.png"
    assert paths[9].name == "article_banner_20251030_120000_10.png"
