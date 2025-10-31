"""DeepAI style configuration loader"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from lib.logger import logger


@dataclass
class DeepAIStyle:
    """DeepAI style configuration"""

    slug: str
    name: str
    description: str
    endpoint: str
    default_params: dict[str, Any]


class DeepAIStyleLoader:
    """Loads and manages DeepAI style configurations from YAML"""

    _instance: "DeepAIStyleLoader | None" = None
    _styles: dict[str, DeepAIStyle] = {}

    def __new__(cls) -> "DeepAIStyleLoader":
        """Singleton pattern to cache loaded styles"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_styles()
        return cls._instance

    def _load_styles(self) -> None:
        """Load styles from YAML file with local override support"""
        # Try to load local override first
        local_path = Path("deepai_styles.local.yaml")
        default_path = Path("deepai_styles.yaml")

        if local_path.exists():
            logger.info(f"Loading DeepAI styles from {local_path}")
            self._styles = self._load_yaml(local_path)
        elif default_path.exists():
            logger.info(f"Loading DeepAI styles from {default_path}")
            self._styles = self._load_yaml(default_path)
        else:
            logger.warning("No deepai_styles.yaml found, using fallback defaults")
            self._styles = self._get_fallback_styles()

    def _load_yaml(self, path: Path) -> dict[str, DeepAIStyle]:
        """Load YAML file and parse into DeepAIStyle objects"""
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

                if not data or "styles" not in data:
                    logger.error(f"Invalid format in {path}, using fallback")
                    return self._get_fallback_styles()

                styles = {}
                for slug, config in data["styles"].items():
                    styles[slug] = DeepAIStyle(
                        slug=slug,
                        name=config.get("name", slug),
                        description=config.get("description", ""),
                        endpoint=config.get("endpoint", slug),
                        default_params=config.get("default_params", {}),
                    )

                logger.info(f"Loaded {len(styles)} DeepAI styles")
                return styles

        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            return self._get_fallback_styles()

    def _get_fallback_styles(self) -> dict[str, DeepAIStyle]:
        """Fallback styles if YAML file is missing"""
        return {
            "origami-3d-generator": DeepAIStyle(
                slug="origami-3d-generator",
                name="3D Origami Generator",
                description="Paper-folded 3D compositions in soft pastel light",
                endpoint="origami-3d-generator",
                default_params={"turbo": True, "genius_preference": "classic"},
            ),
            "text2img": DeepAIStyle(
                slug="text2img",
                name="Text to Image (Simple)",
                description="General-purpose text-to-image generation",
                endpoint="text2img",
                default_params={},
            ),
        }

    def get_style(self, slug: str) -> DeepAIStyle | None:
        """Get style configuration by slug

        Args:
            slug: Style identifier (e.g., 'origami-3d-generator')

        Returns:
            DeepAIStyle object if found, None otherwise
        """
        return self._styles.get(slug)

    def list_styles(self) -> list[DeepAIStyle]:
        """Get list of all available styles

        Returns:
            List of DeepAIStyle objects sorted by name
        """
        return sorted(self._styles.values(), key=lambda s: s.name)

    def get_style_slugs(self) -> list[str]:
        """Get list of style slugs

        Returns:
            List of style slugs sorted alphabetically
        """
        return sorted(self._styles.keys())

    def style_exists(self, slug: str) -> bool:
        """Check if a style exists

        Args:
            slug: Style identifier

        Returns:
            True if style exists, False otherwise
        """
        return slug in self._styles


# Singleton instance for easy access
_loader: DeepAIStyleLoader | None = None


def get_style_loader() -> DeepAIStyleLoader:
    """Get the singleton DeepAIStyleLoader instance"""
    global _loader
    if _loader is None:
        _loader = DeepAIStyleLoader()
    return _loader


__all__ = ["DeepAIStyle", "DeepAIStyleLoader", "get_style_loader"]
