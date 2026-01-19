"""Library scanning and indexing for music files."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4

from .config import Config


@dataclass
class Track:
    """Represents a music track with its metadata."""

    path: Path
    title: str
    artist: str
    album: str
    genre: str
    size_bytes: int
    format: str  # "mp3" or "aac"

    @property
    def size_mb(self) -> float:
        """Return size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def dedupe_key(self) -> str:
        """Key used for deduplication (lowercase title + artist)."""
        return f"{self.title.lower()}|{self.artist.lower()}"


def extract_metadata(file_path: Path) -> Optional[Track]:
    """Extract metadata from a music file using mutagen.

    Returns None if the file can't be read or has no usable metadata.
    """
    try:
        size_bytes = file_path.stat().st_size
        suffix = file_path.suffix.lower()

        # Determine format
        if suffix == ".mp3":
            audio_format = "mp3"
            audio = mutagen.File(file_path, easy=True)
            if audio is None:
                return None

            title = _get_tag(audio, "title", file_path.stem)
            artist = _get_tag(audio, "artist", "Unknown Artist")
            album = _get_tag(audio, "album", "Unknown Album")
            genre = _get_tag(audio, "genre", "Unknown")

        elif suffix in (".m4a", ".aac"):
            audio_format = "aac"
            audio = MP4(file_path)

            # MP4 uses different tag names
            title = _get_mp4_tag(audio, "\xa9nam", file_path.stem)
            artist = _get_mp4_tag(audio, "\xa9ART", "Unknown Artist")
            album = _get_mp4_tag(audio, "\xa9alb", "Unknown Album")
            genre = _get_mp4_tag(audio, "\xa9gen", "Unknown")
        else:
            return None

        return Track(
            path=file_path,
            title=title,
            artist=artist,
            album=album,
            genre=genre,
            size_bytes=size_bytes,
            format=audio_format,
        )

    except Exception:
        # If we can't read the file, skip it
        return None


def _get_tag(audio, tag_name: str, default: str) -> str:
    """Get a tag value from EasyID3/EasyMP4, returning default if missing."""
    values = audio.get(tag_name)
    if values and len(values) > 0:
        return str(values[0]).strip()
    return default


def _get_mp4_tag(audio: MP4, tag_name: str, default: str) -> str:
    """Get a tag value from MP4, returning default if missing."""
    values = audio.tags.get(tag_name) if audio.tags else None
    if values and len(values) > 0:
        return str(values[0]).strip()
    return default


class ScanError:
    """Represents an error encountered while scanning a directory."""

    def __init__(self, path: Path, error_type: str, message: str):
        self.path = path
        self.error_type = error_type  # "not_found" or "permission_denied"
        self.message = message


class ScanResult:
    """Result of scanning a directory."""

    def __init__(self, files: list[Path], error: Optional[ScanError] = None):
        self.files = files
        self.error = error

    @property
    def success(self) -> bool:
        return self.error is None


def check_directory_access(directory: Path) -> Optional[ScanError]:
    """Check if a directory exists and is accessible.

    Returns None if accessible, or a ScanError describing the problem.
    """
    import os

    # First check if parent path is accessible (helps detect mount issues)
    try:
        # Try to access the path
        if not directory.exists():
            # Could be missing OR permission denied - try to distinguish
            parent = directory.parent
            if parent.exists():
                # Parent exists, so this specific path is missing
                return ScanError(
                    directory,
                    "not_found",
                    f"Path not found: {directory}",
                )
            else:
                # Parent doesn't exist - might be unmounted volume
                return ScanError(
                    directory,
                    "not_found",
                    f"Path not found (volume may not be mounted): {directory}",
                )

        # Path exists, now check if we can read it
        if not os.access(directory, os.R_OK):
            return ScanError(
                directory,
                "permission_denied",
                f"Permission denied: {directory} - Grant Full Disk Access to Terminal in System Settings > Privacy & Security",
            )

        # Try to actually list the directory
        try:
            next(directory.iterdir(), None)
        except PermissionError:
            return ScanError(
                directory,
                "permission_denied",
                f"Permission denied: {directory} - Grant Full Disk Access to Terminal in System Settings > Privacy & Security",
            )

        return None

    except PermissionError:
        return ScanError(
            directory,
            "permission_denied",
            f"Permission denied: {directory} - Grant Full Disk Access to Terminal in System Settings > Privacy & Security",
        )
    except OSError as e:
        return ScanError(
            directory,
            "not_found",
            f"Cannot access path: {directory} ({e})",
        )


def scan_directory(
    directory: Path,
    extensions: list[str],
    progress_callback: Optional[Callable[[Path], None]] = None,
) -> ScanResult:
    """Recursively scan a directory for music files.

    Args:
        directory: Root directory to scan.
        extensions: List of file extensions to include (e.g., [".mp3", ".m4a"]).
        progress_callback: Optional callback called for each file found.

    Returns:
        ScanResult with list of paths and any error encountered.
    """
    # Check directory access first
    error = check_directory_access(directory)
    if error:
        return ScanResult([], error)

    files = []
    extensions_lower = [ext.lower() for ext in extensions]

    try:
        for file_path in directory.rglob("*"):
            try:
                if file_path.is_file() and file_path.suffix.lower() in extensions_lower:
                    files.append(file_path)
                    if progress_callback:
                        progress_callback(file_path)
            except PermissionError:
                # Skip files we can't access
                continue

    except PermissionError:
        return ScanResult(
            files,
            ScanError(
                directory,
                "permission_denied",
                f"Permission denied while scanning: {directory}",
            ),
        )

    return ScanResult(files)


class IndexResult:
    """Result of building the music index."""

    def __init__(self, tracks: list[Track], errors: list[ScanError]):
        self.tracks = tracks
        self.errors = errors

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


def build_index(
    config: Config,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> IndexResult:
    """Build a music library index from configured source directories.

    Scans all source directories, extracts metadata, and deduplicates
    based on format preference (keeps AAC or MP3 based on config).

    Args:
        config: Application configuration.
        progress_callback: Optional callback(status_message, current, total).

    Returns:
        IndexResult with tracks and any errors encountered.
    """
    all_files: list[Path] = []
    errors: list[ScanError] = []

    # Scan all source directories
    for source_path in config.source_paths:
        if progress_callback:
            progress_callback(f"Scanning {source_path.name}...", 0, 0)

        result = scan_directory(source_path, config.music_extensions)
        all_files.extend(result.files)

        if result.error:
            errors.append(result.error)

    # Extract metadata from all files
    tracks: list[Track] = []
    total_files = len(all_files)

    for i, file_path in enumerate(all_files):
        if progress_callback:
            progress_callback("Reading metadata...", i + 1, total_files)

        track = extract_metadata(file_path)
        if track:
            tracks.append(track)

    # Deduplicate based on format preference
    deduplicated = _deduplicate_tracks(tracks, config.format_preference)

    return IndexResult(deduplicated, errors)


def _deduplicate_tracks(tracks: list[Track], format_preference: str) -> list[Track]:
    """Remove duplicate tracks, keeping preferred format.

    When the same song exists in both MP3 and AAC, keep the preferred format.

    Args:
        tracks: List of all tracks (may contain duplicates).
        format_preference: "aac" or "mp3" - which format to prefer.

    Returns:
        Deduplicated list of tracks.
    """
    # Group tracks by dedupe key
    seen: dict[str, Track] = {}

    for track in tracks:
        key = track.dedupe_key

        if key not in seen:
            # First time seeing this track
            seen[key] = track
        else:
            # Duplicate found - keep preferred format
            existing = seen[key]

            if format_preference == "aac":
                # Prefer AAC over MP3
                if track.format == "aac" and existing.format == "mp3":
                    seen[key] = track
            else:
                # Prefer MP3 over AAC
                if track.format == "mp3" and existing.format == "aac":
                    seen[key] = track

    return list(seen.values())


# --- Library Cache Functions ---

CACHE_FILENAME = "library_cache.json"


def get_cache_path() -> Path:
    """Get the path to the library cache file."""
    return Path(__file__).parent.parent / CACHE_FILENAME


def cache_exists() -> bool:
    """Check if the library cache file exists."""
    return get_cache_path().exists()


def get_cache_info() -> Optional[dict]:
    """Get cache metadata (date, track count) without loading all tracks.

    Returns None if cache doesn't exist or is invalid.
    """
    cache_path = get_cache_path()
    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "cached_at": data.get("cached_at", "Unknown"),
                "track_count": len(data.get("tracks", [])),
            }
    except (json.JSONDecodeError, KeyError):
        return None


def save_cache(tracks: list[Track]) -> None:
    """Save the library index to a JSON cache file."""
    cache_path = get_cache_path()

    # Convert tracks to JSON-serializable format
    tracks_data = []
    for track in tracks:
        track_dict = asdict(track)
        track_dict["path"] = str(track.path)  # Convert Path to string
        tracks_data.append(track_dict)

    cache_data = {
        "cached_at": datetime.now().isoformat(),
        "track_count": len(tracks),
        "tracks": tracks_data,
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)


def load_cache() -> Optional[list[Track]]:
    """Load the library index from a JSON cache file.

    Returns None if cache doesn't exist or is invalid.
    """
    cache_path = get_cache_path()
    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tracks = []
        for track_dict in data.get("tracks", []):
            track = Track(
                path=Path(track_dict["path"]),
                title=track_dict["title"],
                artist=track_dict["artist"],
                album=track_dict["album"],
                genre=track_dict["genre"],
                size_bytes=track_dict["size_bytes"],
                format=track_dict["format"],
            )
            tracks.append(track)

        return tracks

    except (json.JSONDecodeError, KeyError, TypeError):
        return None
