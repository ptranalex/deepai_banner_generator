"""Prompt template loader for GPT interactions"""

from pathlib import Path
from typing import Any

import yaml

from lib.logger import logger


class PromptLoader:
    """Loads and manages GPT prompt templates from YAML files"""

    _instance: "PromptLoader | None" = None
    _prompts: dict[str, Any] = {}

    def __new__(cls) -> "PromptLoader":
        """Singleton pattern to cache loaded prompts"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_prompts()
        return cls._instance

    def _load_prompts(self) -> None:
        """Load prompts from YAML file with local override support"""
        # Try to load local override first
        local_path = Path("prompts.local.yaml")
        default_path = Path("prompts.yaml")

        if local_path.exists():
            logger.info(f"Loading prompts from {local_path}")
            self._prompts = self._load_yaml(local_path)
        elif default_path.exists():
            logger.info(f"Loading prompts from {default_path}")
            self._prompts = self._load_yaml(default_path)
        else:
            logger.warning("No prompts.yaml found, using fallback defaults")
            self._prompts = self._get_fallback_prompts()

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """Load YAML file and return parsed content"""
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            return self._get_fallback_prompts()

    def _get_fallback_prompts(self) -> dict[str, Any]:
        """Fallback prompts if YAML file is missing"""
        return {
            "simple": {
                "system": "You are a creative prompt generator that turns blog posts into vivid image prompts.",
                "user": "Title: {title}\n\nBlog:\n{content}\n\nGenerate one concise image prompt.",
            },
            "origami": {
                "system": "You are a creative image prompt generator for 3D Origamic style.",
                "user": "Title: {title}\n\nContent:\n{content}\n\nGenerate 10 creative prompts.",
            },
        }

    def get_simple_prompts(self) -> tuple[str, str]:
        """Get simple prompt templates

        Returns:
            Tuple of (system_prompt, user_template)
        """
        simple = self._prompts.get("simple", {})
        system = simple.get("system", "").strip()
        user = simple.get("user", "").strip()
        return system, user

    def get_origami_prompts(self) -> tuple[str, str]:
        """Get origami prompt templates

        Returns:
            Tuple of (system_prompt, user_template)
        """
        origami = self._prompts.get("origami", {})
        system = origami.get("system", "").strip()
        user = origami.get("user", "").strip()
        return system, user

    def format_user_prompt(self, template: str, title: str, content: str) -> str:
        """Format user prompt template with variables

        Args:
            template: Template string with {title} and {content} placeholders
            title: Blog post title
            content: Blog post content

        Returns:
            Formatted prompt string
        """
        return template.format(title=title, content=content)


# Singleton instance for easy access
_loader: PromptLoader | None = None


def get_prompt_loader() -> PromptLoader:
    """Get the singleton PromptLoader instance"""
    global _loader
    if _loader is None:
        _loader = PromptLoader()
    return _loader


__all__ = ["PromptLoader", "get_prompt_loader"]
