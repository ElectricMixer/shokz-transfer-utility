"""File transfer operations for Shokz device."""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .config import Config
from .indexer import Track


@dataclass
class TransferResult:
    """Result of a transfer operation."""

    success: bool
    files_copied: int
    bytes_copied: int
    errors: list[str]

    @property
    def mb_copied(self) -> float:
        """Return megabytes copied."""
        return self.bytes_copied / (1024 * 1024)


@dataclass
class ShokzFile:
    """Represents a file currently on the Shokz device."""

    path: Path
    name: str
    size_bytes: int

    @property
    def size_mb(self) -> float:
        """Return size in megabytes."""
        return self.size_bytes / (1024 * 1024)


def is_shokz_mounted(target_path: Path) -> bool:
    """Check if the Shokz device is mounted.

    Args:
        target_path: Path where Shokz should be mounted.

    Returns:
        True if mounted and accessible.
    """
    return target_path.exists() and target_path.is_dir()


def get_shokz_contents(
    target_path: Path,
    music_extensions: list[str],
) -> list[ShokzFile]:
    """List music files currently on the Shokz device.

    Args:
        target_path: Path to Shokz mount point.
        music_extensions: List of music file extensions.

    Returns:
        List of ShokzFile objects.
    """
    if not is_shokz_mounted(target_path):
        return []

    files = []
    extensions_lower = [ext.lower() for ext in music_extensions]

    for file_path in target_path.rglob("*"):
        # Skip hidden files and directories
        if any(part.startswith(".") for part in file_path.parts):
            continue

        if file_path.is_file() and file_path.suffix.lower() in extensions_lower:
            files.append(
                ShokzFile(
                    path=file_path,
                    name=file_path.name,
                    size_bytes=file_path.stat().st_size,
                )
            )

    return files


def get_shokz_usage(target_path: Path, music_extensions: list[str]) -> tuple[float, int]:
    """Get total size and count of music files on Shokz.

    Args:
        target_path: Path to Shokz mount point.
        music_extensions: List of music file extensions.

    Returns:
        Tuple of (total_mb, file_count).
    """
    files = get_shokz_contents(target_path, music_extensions)
    total_bytes = sum(f.size_bytes for f in files)
    return total_bytes / (1024 * 1024), len(files)


def clear_shokz_music(
    target_path: Path,
    music_extensions: list[str],
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> tuple[int, list[str]]:
    """Remove all music files from Shokz device.

    Preserves system files and hidden files/directories.

    Args:
        target_path: Path to Shokz mount point.
        music_extensions: List of music file extensions to remove.
        progress_callback: Optional callback(filename, current, total).

    Returns:
        Tuple of (files_deleted, list_of_errors).
    """
    if not is_shokz_mounted(target_path):
        return 0, ["Shokz device not mounted"]

    files = get_shokz_contents(target_path, music_extensions)
    total = len(files)
    deleted = 0
    errors = []

    for i, shokz_file in enumerate(files):
        if progress_callback:
            progress_callback(shokz_file.name, i + 1, total)

        try:
            shokz_file.path.unlink()
            deleted += 1
        except OSError as e:
            errors.append(f"Failed to delete {shokz_file.name}: {e}")

    # Clean up empty directories (but not the root or hidden dirs)
    _remove_empty_dirs(target_path)

    return deleted, errors


def _remove_empty_dirs(root_path: Path) -> None:
    """Remove empty directories under root_path.

    Preserves the root directory and hidden directories.
    """
    # Walk bottom-up to remove empty dirs
    for dir_path in sorted(root_path.rglob("*"), reverse=True):
        # Skip hidden directories
        if any(part.startswith(".") for part in dir_path.parts):
            continue

        if dir_path.is_dir():
            try:
                # Only removes if empty
                dir_path.rmdir()
            except OSError:
                # Directory not empty or other error - skip
                pass


def transfer_to_shokz(
    tracks: list[Track],
    target_path: Path,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> TransferResult:
    """Copy tracks to Shokz device.

    Files are copied to the root of the device with their original names.
    If duplicate names exist, a number suffix is added.

    Args:
        tracks: List of tracks to copy.
        target_path: Path to Shokz mount point.
        progress_callback: Optional callback(filename, current, total).

    Returns:
        TransferResult with success status and statistics.
    """
    if not is_shokz_mounted(target_path):
        return TransferResult(
            success=False,
            files_copied=0,
            bytes_copied=0,
            errors=["Shokz device not mounted"],
        )

    total = len(tracks)
    copied = 0
    bytes_copied = 0
    errors = []
    used_names: set[str] = set()

    for i, track in enumerate(tracks):
        if progress_callback:
            progress_callback(track.title, i + 1, total)

        # Generate unique filename
        dest_name = _get_unique_filename(track.path.name, used_names)
        used_names.add(dest_name.lower())
        dest_path = target_path / dest_name

        try:
            shutil.copy2(track.path, dest_path)
            copied += 1
            bytes_copied += track.size_bytes
        except OSError as e:
            errors.append(f"Failed to copy {track.title}: {e}")

    return TransferResult(
        success=len(errors) == 0,
        files_copied=copied,
        bytes_copied=bytes_copied,
        errors=errors,
    )


def _get_unique_filename(original_name: str, used_names: set[str]) -> str:
    """Generate a unique filename, adding number suffix if needed.

    Args:
        original_name: Original filename.
        used_names: Set of already used names (lowercase).

    Returns:
        Unique filename.
    """
    if original_name.lower() not in used_names:
        return original_name

    # Split name and extension
    path = Path(original_name)
    stem = path.stem
    suffix = path.suffix

    # Try adding numbers until unique
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        if new_name.lower() not in used_names:
            return new_name
        counter += 1


def perform_full_transfer(
    tracks: list[Track],
    config: Config,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    status_callback: Optional[Callable[[str], None]] = None,
) -> TransferResult:
    """Perform a complete transfer: clear Shokz then copy new files.

    Args:
        tracks: List of tracks to transfer.
        config: Application configuration.
        progress_callback: Optional callback(item_name, current, total).
        status_callback: Optional callback(status_message).

    Returns:
        TransferResult with success status and statistics.
    """
    target = config.target

    # Check mount
    if not is_shokz_mounted(target):
        return TransferResult(
            success=False,
            files_copied=0,
            bytes_copied=0,
            errors=["Shokz device not mounted at " + str(target)],
        )

    # Clear existing music
    if status_callback:
        status_callback("Clearing existing music files...")

    deleted, clear_errors = clear_shokz_music(
        target,
        config.music_extensions,
        progress_callback,
    )

    if clear_errors:
        return TransferResult(
            success=False,
            files_copied=0,
            bytes_copied=0,
            errors=clear_errors,
        )

    # Transfer new files
    if status_callback:
        status_callback("Copying new files...")

    result = transfer_to_shokz(tracks, target, progress_callback)

    return result


def archive_shokz_contents(
    config: Config,
    archive_dir: Optional[Path] = None,
) -> tuple[bool, str]:
    """Save current Shokz contents to a JSON archive file.

    Args:
        config: Application configuration.
        archive_dir: Directory to save archives. Defaults to 'archives/' in project root.

    Returns:
        Tuple of (success, message_or_filepath).
    """
    if not is_shokz_mounted(config.target):
        return False, "Shokz device not mounted"

    files = get_shokz_contents(config.target, config.music_extensions)

    if not files:
        return False, "No music files on Shokz to archive"

    # Default archive directory
    if archive_dir is None:
        archive_dir = Path(__file__).parent.parent / "archives"

    # Create directory if needed
    archive_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"shokz_archive_{timestamp}.json"
    filepath = archive_dir / filename

    # Build archive data
    total_bytes = sum(f.size_bytes for f in files)
    archive_data = {
        "archived_at": datetime.now().isoformat(),
        "file_count": len(files),
        "total_size_mb": round(total_bytes / (1024 * 1024), 2),
        "files": [
            {
                "filename": f.name,
                "size_mb": round(f.size_mb, 2),
            }
            for f in sorted(files, key=lambda x: x.name.lower())
        ],
    }

    # Write file
    try:
        with open(filepath, "w") as f:
            json.dump(archive_data, f, indent=2)
            f.write("\n")
        return True, str(filepath)
    except OSError as e:
        return False, f"Failed to write archive: {e}"
