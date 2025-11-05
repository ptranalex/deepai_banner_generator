"""DeepAI client for image generation with async support"""

import asyncio
import uuid
from pathlib import Path
from typing import Any, Literal

import aiofiles
import aiohttp

from lib.config import get_settings
from lib.deepai.styles import get_style_loader
from lib.logger import logger


class DeepAIClient:
    """Client for DeepAI API interactions with async support"""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize DeepAI client

        Args:
            api_key: DeepAI API key (uses config if not provided)
        """
        settings = get_settings()
        self.api_key = api_key or settings.deepai_api_key
        self.base_api_url = "https://api.deepai.org/api"
        self.timeout = settings.deepai_timeout
        self.max_retries = settings.deepai_max_retries
        self.retry_base_delay = settings.deepai_retry_base_delay
        self.max_concurrent = settings.deepai_max_concurrent
        self.style_loader = get_style_loader()
        logger.info("Initialized DeepAI client")

    async def generate_image(
        self,
        prompt: str,
        deepai_style: str = "origami-3d-generator",
        width: int = 1792,
        height: int = 1024,
        version: Literal["standard", "hd", "genius"] = "standard",
        **extra_params: Any,
    ) -> str | None:
        """Generate image and return URL (async)

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
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        prompt_length = len(prompt)

        logger.info(
            f"[{request_id}] Generating image with style '{deepai_style}' "
            f"(prompt: {prompt_length} chars): {prompt[:50]}..."
        )

        # Load style configuration
        style = self.style_loader.get_style(deepai_style)
        if not style:
            logger.warning(
                f"[{request_id}] Unknown style '{deepai_style}', falling back to text2img"
            )
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
        logger.debug(f"[{request_id}] API URL: {api_url}")
        logger.debug(f"[{request_id}] Style: {style.name if style else 'text2img'}")
        logger.debug(f"[{request_id}] Request data: {data}")

        # Retry loop with exponential backoff
        async with aiohttp.ClientSession() as session:
            for attempt in range(1, self.max_retries + 1):
                start_time = asyncio.get_event_loop().time()

                try:
                    # Convert data dict to FormData for aiohttp
                    form_data = aiohttp.FormData()
                    for key, value in data.items():
                        form_data.add_field(key, value)

                    async with session.post(
                        api_url,
                        headers=headers,
                        data=form_data,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as response:
                        elapsed = asyncio.get_event_loop().time() - start_time

                        if response.status == 200:
                            result = await response.json()
                            image_url: str | None = result.get("output_url")
                            logger.info(
                                f"[{request_id}] Image generated successfully in {elapsed:.1f}s "
                                f"(attempt {attempt}/{self.max_retries}): {image_url}"
                            )
                            return image_url
                        else:
                            response_text = await response.text()
                            logger.warning(
                                f"[{request_id}] API request failed (attempt {attempt}/{self.max_retries}) "
                                f"after {elapsed:.1f}s - Status {response.status}: {response_text}"
                            )

                            if attempt < self.max_retries:
                                delay = self.retry_base_delay * (2 ** (attempt - 1))
                                logger.info(f"[{request_id}] Retrying in {delay}s...")
                                await asyncio.sleep(delay)
                            else:
                                logger.error(
                                    f"[{request_id}] All {self.max_retries} attempts failed"
                                )
                                logger.error(f"[{request_id}] Final response: {response_text}")
                                logger.error(f"[{request_id}] Request parameters: {data}")
                                return None

                except (TimeoutError, aiohttp.ClientError) as e:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    logger.warning(
                        f"[{request_id}] Request exception (attempt {attempt}/{self.max_retries}) "
                        f"after {elapsed:.1f}s: {e}"
                    )

                    if attempt < self.max_retries:
                        delay = self.retry_base_delay * (2 ** (attempt - 1))
                        logger.info(f"[{request_id}] Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"[{request_id}] All {self.max_retries} attempts failed due to exceptions"
                        )
                        return None

        return None

    async def download_image(self, url: str, output_path: Path) -> bool:
        """Download image from URL to file (async)

        Args:
            url: Image URL
            output_path: Output file path

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Downloading image from {url} to {output_path}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        content = await response.read()
                        async with aiofiles.open(output_path, "wb") as f:
                            await f.write(content)
                        logger.info(f"Image saved successfully to {output_path}")
                        return True
                    else:
                        logger.error(f"Failed to download image: HTTP {response.status}")
                        return False

        except (TimeoutError, aiohttp.ClientError) as e:
            logger.error(f"Request exception during image download: {e}")
            return False

    async def generate_and_save(
        self,
        prompt: str,
        output_path: Path,
        deepai_style: str = "origami-3d-generator",
        width: int = 1792,
        height: int = 1024,
        version: Literal["standard", "hd", "genius"] = "standard",
        **extra_params: Any,
    ) -> bool:
        """Generate and save image in one call (async)

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
        image_url = await self.generate_image(
            prompt, deepai_style, width, height, version, **extra_params
        )

        if not image_url:
            logger.error("Image generation failed, cannot save")
            return False

        # Download and save
        return await self.download_image(image_url, output_path)

    async def generate_batch(
        self,
        batch_data: list[dict[str, Any]],
        max_concurrent: int | None = None,
    ) -> list[bool]:
        """Generate multiple images with controlled concurrency (async)

        Args:
            batch_data: List of dicts with keys: prompt, output_path,
                        deepai_style, width, height, version, and any extra_params
            max_concurrent: Max concurrent requests (default from config)

        Returns:
            List of success/failure for each image
        """
        if max_concurrent is None:
            max_concurrent = self.max_concurrent

        logger.info(
            f"Starting batch generation: {len(batch_data)} images, max {max_concurrent} concurrent"
        )

        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_generate(data: dict[str, Any]) -> bool:
            """Generate with semaphore limit"""
            async with semaphore:
                return await self.generate_and_save(**data)

        tasks = [bounded_generate(data) for data in batch_data]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        successful = sum(1 for r in results if r)
        logger.info(f"Batch generation complete: {successful}/{len(results)} successful")

        return list(results)


__all__ = ["DeepAIClient"]
