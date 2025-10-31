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

    def generate_simple_prompt(self, title: str, content: str) -> str:
        """Generate a single banner prompt

        Args:
            title: Blog post title
            content: Full blog post content

        Returns:
            Generated prompt string
        """
        logger.info(f"Generating simple prompt for: {title}")

        # Load prompts from YAML
        system_prompt, user_template = self.prompt_loader.get_simple_prompts()
        user_prompt = self.prompt_loader.format_user_prompt(user_template, title, content)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
            )

            prompt = response.choices[0].message.content
            if not prompt:
                raise ValueError("Empty response from OpenAI")
            result = prompt.strip()
            # Remove quotes if present
            result = result.strip('"').strip("'")
            logger.info(f"Generated simple prompt: {result[:50]}...")
            return result

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

        # Load prompts from YAML
        system_prompt, user_template = self.prompt_loader.get_origami_prompts()
        user_prompt = self.prompt_loader.format_user_prompt(user_template, title, content)

        system_msg = {"role": "system", "content": system_prompt}
        user_msg = {"role": "user", "content": user_prompt}

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[system_msg, user_msg],  # type: ignore
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
                # Remove leading number and separators like "1.", "1)", "1-" And all quotes
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
