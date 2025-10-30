"""OpenAI GPT client for prompt generation"""

import sys

from openai import OpenAI

from lib.config import get_settings
from lib.logger import logger


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
        logger.info(f"Initialized GPT client with model: {self.model}")

    def generate_simple_prompt(self, title: str, content: str) -> str:
        """Generate a single banner prompt

        Args:
            title: Blog post title
            content: Full blog post content

        Returns:
            Generated prompt string
        """
        logger.info(f"Generating simple prompt for: {title}")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a creative prompt generator that turns full blog posts "
                    "into vivid image prompts for DeepAI. Focus on mood, emotion, and symbolic visuals."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Title: {title}\n\n"
                    f"Blog:\n{content}\n\n"
                    f"Generate one concise image prompt for DeepAI (suitable for a banner)."
                ),
            },
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
            )

            prompt = response.choices[0].message.content
            if not prompt:
                raise ValueError("Empty response from OpenAI")
            prompt = prompt.strip()
            # Remove quotes if present
            prompt = prompt.strip('"').strip("'")
            logger.info(f"Generated simple prompt: {prompt[:50]}...")
            return prompt

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            print(f"Error calling OpenAI API: {e}")
            sys.exit(1)

    def generate_origami_prompts(self, title: str, content: str) -> list[str]:
        """Generate 10 origami-style banner prompts

        Args:
            title: Blog post title
            content: Full blog post content

        Returns:
            List of 10 generated prompts
        """
        logger.info(f"Generating origami prompts for: {title}")

        system_msg = {
            "role": "system",
            "content": (
                "You are a creative image prompt generator for DeepAI's 3D Origamic style. "
                "Given a blog title and full content, create 10 unique, vivid prompts suitable for banner images. "
                "Each prompt should: "
                "1) Capture the blog's emotion and theme, "
                "2) Use 3D origami, paper folds, or transformation as metaphors, "
                "3) Describe soft pastel colors and cinematic composition, "
                "4) Avoid text or captions, "
                "5) Be concise and art-directable. "
                "Output format: a clean numbered list of 10 prompts. No commentary."
            ),
        }

        user_msg = {
            "role": "user",
            "content": (
                f"Title: {title}\n\n"
                f"Full blog content:\n{content}\n\n"
                f"Generate 10 creative 3D origamic prompts now."
            ),
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[system_msg, user_msg],  # type: ignore[list-item]
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
                for i in range(1, 11):
                    prefixes = [f"{i}.", f"{i})", f"{i} -", f"{i}-"]
                    for prefix in prefixes:
                        if line.startswith(prefix):
                            line = line[len(prefix) :].strip()
                            break
                prompts.append(line.strip('" '))

            logger.info(f"Generated {len(prompts)} origami prompts")
            return prompts[:10]  # Return first 10

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            print(f"Error calling OpenAI API: {e}")
            sys.exit(1)


__all__ = ["GPTClient"]
