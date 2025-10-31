"""OpenAI GPT client for prompt generation"""

import sys

from openai import OpenAI

from lib.config import get_settings
from lib.logger import logger
from lib.prompts import get_prompt_loader


class GPTClient:
    """Client for OpenAI GPT API interactions"""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize GPT client

        Args:
            api_key: OpenAI API key (uses config if not provided)
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.client = OpenAI(api_key=self.api_key)
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens
        self.prompt_loader = get_prompt_loader()
        logger.info(f"Initialized GPT client with model: {self.model}")

    def generate_prompts(
        self,
        title: str,
        content: str,
        deepai_style_slug: str,
        num_prompts: int = 10,
    ) -> list[str]:
        """Generate style-aware banner prompts

        Args:
            title: Blog post title
            content: Full blog post content
            deepai_style_slug: DeepAI style slug (e.g., 'origami-3d-generator')
            num_prompts: Number of prompts to generate (default: 10)

        Returns:
            List of generated prompts
        """
        logger.info(
            f"Generating {num_prompts} prompts for '{title}' in style '{deepai_style_slug}'"
        )

        # Get style description from DeepAIStyleLoader
        from lib.deepai import get_style_loader

        style_loader = get_style_loader()
        deepai_style = style_loader.get_style(deepai_style_slug)
        style_description = (
            deepai_style.description if deepai_style else "General-purpose image generation"
        )

        # Load base template from YAML
        prompts_dict = self.prompt_loader._prompts.get("base", {})
        system_prompt = prompts_dict.get("system", "").strip()
        user_template = prompts_dict.get("user", "").strip()

        if not system_prompt or not user_template:
            logger.error("Base template not found in prompts.yaml")
            raise ValueError("Base template not found in prompts.yaml")

        # Format user prompt with all variables (YAML uses 'count' not 'num_prompts')
        user_prompt = user_template.format(
            style=deepai_style_slug,
            style_description=style_description,
            title=title,
            content=content,
            count=num_prompts,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            raw_output = response.choices[0].message.content
            if not raw_output:
                raise ValueError("Empty response from OpenAI")

            # Parse numbered list into list of strings
            prompts = []
            for line in raw_output.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Remove leading number and separators like "1.", "1)", "1-"
                for i in range(1, num_prompts + 1):
                    prefixes = [f"{i}.", f"{i})", f"{i} -", f"{i}-"]
                    for prefix in prefixes:
                        if line.startswith(prefix):
                            line = line[len(prefix) :].strip()
                            break
                # Remove quotes
                prompts.append(line.strip('" '))

            logger.info(f"Generated {len(prompts)} prompts")
            return prompts[:num_prompts]  # Return requested count

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            print(f"Error calling OpenAI API: {e}")
            sys.exit(1)


__all__ = ["GPTClient"]
