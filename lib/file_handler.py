"""File handling utilities for markdown and output files"""

from datetime import datetime
from pathlib import Path

import yaml

from lib.logger import logger


class MarkdownHandler:
    """Handles markdown file operations"""

    @staticmethod
    def find_markdown_files(directory: Path) -> list[Path]:
        """Find all markdown files in directory

        Args:
            directory: Directory to search

        Returns:
            List of markdown file paths
        """
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return []

        markdown_files = sorted(directory.glob("*.md"))
        logger.debug(f"Found {len(markdown_files)} markdown files in {directory}")
        return markdown_files

    @staticmethod
    def parse_markdown_post(file_path: Path) -> tuple[dict, str]:
        """Parse markdown file with YAML front matter

        Args:
            file_path: Path to markdown file

        Returns:
            Tuple of (front_matter_dict, body_text)
        """
        logger.debug(f"Parsing markdown file: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        # Check for YAML front matter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                # Front matter exists
                front_matter_str = parts[1].strip()
                body = parts[2].strip()

                try:
                    front_matter = yaml.safe_load(front_matter_str) or {}
                except yaml.YAMLError as e:
                    logger.warning(f"Failed to parse YAML front matter: {e}")
                    front_matter = {}

                return front_matter, body

        # No front matter
        return {}, content.strip()


class OutputHandler:
    """Handles output file organization"""

    @staticmethod
    def generate_output_path(input_file: Path, output_dir: Path, suffix: str = "_banner") -> Path:
        """Generate output path from input file

        Args:
            input_file: Input file path
            output_dir: Output directory
            suffix: Suffix to add to filename

        Returns:
            Generated output path
        """
        return output_dir / f"{input_file.stem}{suffix}.png"

    @staticmethod
    def generate_batch_output_paths(
        input_file: Path,
        output_dir: Path,
        count: int,
        timestamp: str | None = None,
    ) -> list[Path]:
        """Generate multiple output paths for batch generation

        Uses timestamp-based naming: {stem}_banner_{timestamp}_{seq}.png

        Args:
            input_file: Source markdown file
            output_dir: Output directory
            count: Number of files to generate
            timestamp: Optional timestamp string (auto-generated if None)

        Returns:
            List of output paths with sequential naming

        Example:
            >>> generate_batch_output_paths(Path("my-post.md"), Path("out"), 3)
            [
                Path("out/my-post_banner_20251030_143022_01.png"),
                Path("out/my-post_banner_20251030_143022_02.png"),
                Path("out/my-post_banner_20251030_143022_03.png"),
            ]
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        paths = []
        for seq in range(1, count + 1):
            filename = f"{input_file.stem}_banner_{timestamp}_{seq:02d}.png"
            paths.append(output_dir / filename)

        logger.debug(f"Generated {count} batch output paths with timestamp {timestamp}")
        return paths

    @staticmethod
    def ensure_output_directory(path: Path) -> None:
        """Create output directory if it doesn't exist

        Args:
            path: Path to check/create
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured output directory exists: {path.parent}")


__all__ = ["MarkdownHandler", "OutputHandler"]
