"""DeepAI client for image generation"""

from pathlib import Path
from typing import Literal

import requests

from lib.config import get_settings
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
        self.api_url = settings.deepai_api_url
        self.timeout = settings.deepai_timeout
        logger.info("Initialized DeepAI client")

    def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 512,
        version: Literal["standard", "hd", "genius"] = "standard",
    ) -> str | None:
        """Generate image and return URL

        Args:
            prompt: Text prompt for image generation
            width: Image width in pixels
            height: Image height in pixels
            version: Generation version

        Returns:
            Image URL if successful, None otherwise
        """
        logger.info(f"Generating image with prompt: {prompt[:50]}...")

        headers = {"api-key": self.api_key}
        data = {
            "text": prompt,
            "width": str(width),
            "height": str(height),
            "image_generator_version": version,
        }

        try:
            response = requests.post(
                self.api_url,
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
        width: int = 1024,
        height: int = 512,
        version: Literal["standard", "hd", "genius"] = "standard",
    ) -> bool:
        """Generate and save image in one call

        Args:
            prompt: Text prompt
            output_path: Output file path
            width: Image width
            height: Image height
            version: Generation version

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Generating and saving image to {output_path}")

        # Generate image
        image_url = self.generate_image(prompt, width, height, version)

        if not image_url:
            logger.error("Image generation failed, cannot save")
            return False

        # Download and save
        return self.download_image(image_url, output_path)


__all__ = ["DeepAIClient"]
