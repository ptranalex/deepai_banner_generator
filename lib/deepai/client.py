"""DeepAI client for image generation"""

from pathlib import Path
from typing import Any, Literal

import requests

from lib.config import get_settings
from lib.deepai.styles import get_style_loader
from lib.logger import logger


class DeepAIClient:
    """Client for DeepAI API interactions"""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize DeepAI client

        Args:
            api_key: DeepAI API key (uses config if not provided)
        """
        settings = get_settings()
        self.api_key = api_key or settings.deepai_api_key
        self.base_api_url = "https://api.deepai.org/api"
        self.timeout = settings.deepai_timeout
        self.style_loader = get_style_loader()
        logger.info("Initialized DeepAI client")

    def generate_image(
        self,
        prompt: str,
        deepai_style: str = "origami-3d-generator",
        width: int = 1792,
        height: int = 1024,
        version: Literal["standard", "hd", "genius"] = "standard",
        **extra_params: Any,
    ) -> str | None:
        """Generate image and return URL

        Args:
            prompt: Text prompt for image generation
            deepai_style: DeepAI style slug (e.g., 'origami-3d-generator')
            width: Image width in pixels
            height: Image height in pixels
            version: Generation version (case-insensitive, will be capitalized)
            **extra_params: Additional style-specific parameters (e.g., turbo, genius_preference)

        Returns:
            Image URL if successful, None otherwise
        """
        logger.info(f"Generating image with style '{deepai_style}': {prompt[:50]}...")

        # Load style configuration
        style = self.style_loader.get_style(deepai_style)
        if not style:
            logger.warning(f"Unknown style '{deepai_style}', falling back to text2img")
            endpoint = "text2img"
            default_params = {}
        else:
            endpoint = style.endpoint
            default_params = style.default_params.copy()

        # Build API URL
        api_url = f"{self.base_api_url}/{endpoint}"
        headers = {"api-key": self.api_key}

        # Build request data starting with defaults
        data: dict[str, Any] = {
            "text": prompt,
            "width": str(width),
            "height": str(height),
        }

        # Add style-specific default parameters
        for key, value in default_params.items():
            if key not in data:
                data[key] = str(value).lower() if isinstance(value, bool) else str(value)

        # Add extra parameters (override defaults)
        for key, value in extra_params.items():
            data[key] = str(value).lower() if isinstance(value, bool) else str(value)

        # Handle image_generator_version parameter
        # Generic text2img endpoint requires capitalized: "Standard", "Hd", "Genius"
        # Style-specific endpoints require lowercase: "standard", "hd", "genius"
        if version != "standard":
            if endpoint == "text2img":
                # Generic endpoint: capitalize
                data["image_generator_version"] = version.capitalize()
            else:
                # Style-specific endpoints: lowercase
                data["image_generator_version"] = version.lower()

                # When using genius with style-specific endpoints, these params are required
                if version == "genius":
                    if "turbo" not in data:
                        data["turbo"] = "true"
                    if "genius_preference" not in data:
                        data["genius_preference"] = "classic"

        # Debug logging
        logger.debug(f"API URL: {api_url}")
        logger.debug(f"Style: {style.name if style else 'text2img'}")
        logger.debug(f"Request data: {data}")
        logger.debug(f"Full prompt: {prompt}")

        try:
            response = requests.post(
                api_url,
                headers=headers,
                data=data,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                result = response.json()
                image_url: str | None = result.get("output_url")
                logger.info(f"Image generated successfully: {image_url}")
                return image_url
            else:
                logger.error(
                    f"API request failed with status {response.status_code}: {response.text}"
                )
                logger.error(f"Request parameters: {data}")
                return None

        except requests.RequestException as e:
            logger.error(f"Request exception during image generation: {e}")
            return None

    def download_image(self, url: str, output_path: Path) -> bool:
        """Download image from URL to file

        Args:
            url: Image URL
            output_path: Output file path

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Downloading image from {url} to {output_path}")

        try:
            response = requests.get(url, timeout=self.timeout)

            if response.status_code == 200:
                output_path.write_bytes(response.content)
                logger.info(f"Image saved successfully to {output_path}")
                return True
            else:
                logger.error(f"Failed to download image: HTTP {response.status_code}")
                return False

        except requests.RequestException as e:
            logger.error(f"Request exception during image download: {e}")
            return False

    def generate_and_save(
        self,
        prompt: str,
        output_path: Path,
        deepai_style: str = "origami-3d-generator",
        width: int = 1792,
        height: int = 1024,
        version: Literal["standard", "hd", "genius"] = "standard",
        **extra_params: Any,
    ) -> bool:
        """Generate and save image in one call

        Args:
            prompt: Text prompt
            output_path: Output file path
            deepai_style: DeepAI style slug
            width: Image width
            height: Image height
            version: Generation version
            **extra_params: Additional style-specific parameters

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Generating and saving image to {output_path}")

        # Generate image
        image_url = self.generate_image(
            prompt, deepai_style, width, height, version, **extra_params
        )

        if not image_url:
            logger.error("Image generation failed, cannot save")
            return False

        # Download and save
        return self.download_image(image_url, output_path)


__all__ = ["DeepAIClient"]
