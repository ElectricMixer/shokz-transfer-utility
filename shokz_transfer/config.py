"""Configuration management for Shokz Transfer Utility."""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Default config file location (project root)
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.json"


@dataclass
class Config:
    """Application configuration."""

    primary_source: Path
    secondary_source: Path
    target: Path
    capacity_mb: int
    format_preference: str  # "aac" or "mp3"
    music_extensions: list[str] = field(default_factory=lambda: [".mp3", ".m4a", ".aac"])

    @property
    def source_paths(self) -> list[Path]:
        """Return list of all source paths."""
        return [self.primary_source, self.secondary_source]

    @property
    def capacity_bytes(self) -> int:
        """Return capacity in bytes."""
        return self.capacity_mb * 1024 * 1024


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from JSON file."""
    path = config_path or DEFAULT_CONFIG_PATH

    with open(path, "r") as f:
        data = json.load(f)

    return Config(
        primary_source=Path(data["sources"]["primary"]),
        secondary_source=Path(data["sources"]["secondary"]),
        target=Path(data["target"]),
        capacity_mb=data["capacity_mb"],
        format_preference=data["format_preference"],
        music_extensions=data.get("music_extensions", [".mp3", ".m4a", ".aac"]),
    )


def save_config(config: Config, config_path: Optional[Path] = None) -> None:
    """Save configuration to JSON file."""
    path = config_path or DEFAULT_CONFIG_PATH

    data = {
        "sources": {
            "primary": str(config.primary_source),
            "secondary": str(config.secondary_source),
        },
        "target": str(config.target),
        "capacity_mb": config.capacity_mb,
        "format_preference": config.format_preference,
        "music_extensions": config.music_extensions,
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
