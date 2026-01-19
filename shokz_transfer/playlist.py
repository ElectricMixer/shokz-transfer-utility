"""Playlist management for track selection."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .indexer import Track


# Session file for playlist persistence
SESSION_FILENAME = "playlist_session.json"


def get_session_path() -> Path:
    """Get the path to the playlist session file."""
    return Path(__file__).parent.parent / SESSION_FILENAME


def session_exists() -> bool:
    """Check if a saved playlist session exists."""
    return get_session_path().exists()


def get_session_info() -> Optional[dict]:
    """Get session metadata (date, track count, size) without loading all tracks.

    Returns None if session doesn't exist or is invalid.
    """
    session_path = get_session_path()
    if not session_path.exists():
        return None

    try:
        with open(session_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "saved_at": data.get("saved_at", "Unknown"),
                "track_count": data.get("track_count", 0),
                "total_size_mb": data.get("total_size_mb", 0),
            }
    except (json.JSONDecodeError, KeyError):
        return None


def save_session(playlist: "Playlist") -> bool:
    """Save the current playlist to a session file.

    Args:
        playlist: The playlist to save.

    Returns:
        True if saved successfully, False otherwise.
    """
    session_path = get_session_path()

    # Convert tracks to JSON-serializable format
    tracks_data = []
    for track in playlist._tracks:
        tracks_data.append({
            "path": str(track.path),
            "title": track.title,
            "artist": track.artist,
            "album": track.album,
            "genre": track.genre,
            "size_bytes": track.size_bytes,
            "format": track.format,
        })

    session_data = {
        "saved_at": datetime.now().isoformat(),
        "track_count": playlist.count,
        "total_size_mb": round(playlist.total_size_mb, 2),
        "capacity_mb": playlist.capacity_mb,
        "tracks": tracks_data,
    }

    try:
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)
        return True
    except (IOError, OSError):
        return False


def load_session() -> Optional["Playlist"]:
    """Load a saved playlist session.

    Returns None if session doesn't exist or is invalid.
    """
    session_path = get_session_path()
    if not session_path.exists():
        return None

    try:
        with open(session_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Reconstruct playlist
        capacity = data.get("capacity_mb", 4000)
        playlist = Playlist(capacity_mb=capacity)

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
            playlist._tracks.append(track)

        return playlist

    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def clear_session() -> bool:
    """Delete the session file after successful transfer.

    Returns:
        True if deleted or didn't exist, False on error.
    """
    session_path = get_session_path()
    if not session_path.exists():
        return True

    try:
        session_path.unlink()
        return True
    except (IOError, OSError):
        return False


@dataclass
class Playlist:
    """Manages a collection of tracks for transfer to Shokz."""

    capacity_mb: int = 4000
    _tracks: list[Track] = field(default_factory=list)

    @property
    def tracks(self) -> list[Track]:
        """Return a copy of the track list."""
        return list(self._tracks)

    @property
    def count(self) -> int:
        """Return number of tracks in playlist."""
        return len(self._tracks)

    @property
    def total_size_bytes(self) -> int:
        """Return total size of all tracks in bytes."""
        return sum(t.size_bytes for t in self._tracks)

    @property
    def total_size_mb(self) -> float:
        """Return total size of all tracks in MB."""
        return self.total_size_bytes / (1024 * 1024)

    @property
    def remaining_mb(self) -> float:
        """Return remaining capacity in MB."""
        return self.capacity_mb - self.total_size_mb

    @property
    def percent_full(self) -> float:
        """Return percentage of capacity used."""
        if self.capacity_mb == 0:
            return 100.0
        return (self.total_size_mb / self.capacity_mb) * 100

    @property
    def is_over_capacity(self) -> bool:
        """Return True if playlist exceeds capacity."""
        return self.total_size_mb > self.capacity_mb

    @property
    def is_near_capacity(self) -> bool:
        """Return True if playlist is over 90% of capacity."""
        return self.percent_full > 90

    def add(self, track: Track) -> bool:
        """Add a track to the playlist.

        Avoids adding duplicates (same file path).

        Args:
            track: Track to add.

        Returns:
            True if added, False if already in playlist.
        """
        # Check for duplicate by path
        for existing in self._tracks:
            if existing.path == track.path:
                return False

        self._tracks.append(track)
        return True

    def add_many(self, tracks: list[Track]) -> int:
        """Add multiple tracks to the playlist.

        Args:
            tracks: List of tracks to add.

        Returns:
            Number of tracks actually added (excludes duplicates).
        """
        added = 0
        for track in tracks:
            if self.add(track):
                added += 1
        return added

    def remove(self, index: int) -> Optional[Track]:
        """Remove a track by index.

        Args:
            index: 0-based index of track to remove.

        Returns:
            The removed track, or None if index invalid.
        """
        if 0 <= index < len(self._tracks):
            return self._tracks.pop(index)
        return None

    def remove_many(self, indices: list[int]) -> list[Track]:
        """Remove multiple tracks by index.

        Args:
            indices: List of 0-based indices to remove.

        Returns:
            List of removed tracks.
        """
        # Sort indices in reverse order to avoid index shifting issues
        removed = []
        for index in sorted(indices, reverse=True):
            track = self.remove(index)
            if track:
                removed.append(track)
        return removed

    def clear(self) -> int:
        """Remove all tracks from playlist.

        Returns:
            Number of tracks that were removed.
        """
        count = len(self._tracks)
        self._tracks.clear()
        return count

    def get_status_message(self) -> str:
        """Return a status message about the playlist."""
        if self.count == 0:
            return "Playlist is empty"

        status = f"{self.count} tracks, {self.total_size_mb:.1f} MB / {self.capacity_mb} MB ({self.percent_full:.0f}%)"

        if self.is_over_capacity:
            status += " - OVER CAPACITY!"
        elif self.is_near_capacity:
            status += " - Nearly full"

        return status
