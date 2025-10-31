"""Application configuration with Pydantic settings"""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file"""

    # API Keys (required)
    openai_api_key: str = Field(..., min_length=20, description="OpenAI API key")
    deepai_api_key: str = Field(..., min_length=20, description="DeepAI API key")

    # OpenAI Configuration
    openai_model: str = Field("gpt-4o", description="OpenAI model to use")
    openai_temperature: float = Field(0.9, ge=0.0, le=2.0, description="Temperature for prompts")
    openai_max_tokens: int = Field(1000, ge=1, le=4000, description="Max tokens for responses")

    # DeepAI Configuration
    deepai_api_url: str = "https://api.deepai.org/api/text2img"
    deepai_timeout: int = Field(60, ge=10, le=300, description="Request timeout in seconds")

    # Application Defaults
    default_input_dir: Path = Path("./posts")
    default_output_dir: Path = Path("./banners")
    default_width: int = Field(1792, ge=128, le=2048, description="Default banner width")
    default_height: int = Field(1024, ge=128, le=2048, description="Default banner height")
    default_style: Literal["simple", "origami"] = "origami"
    default_version: Literal["standard", "hd", "genius"] = "standard"
    default_deepai_style: str = "origami-3d-generator"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("default_width", "default_height")
    @classmethod
    def validate_multiple_of_32(cls, v: int) -> int:
        """Validate dimensions are multiples of 32"""
        if v % 32 != 0:
            raise ValueError(f"Must be multiple of 32, got {v}")
        return v


# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get settings singleton (lazy loaded)"""
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings


__all__ = ["Settings", "get_settings"]
