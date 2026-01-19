"""Playlist management for track selection."""

from dataclasses import dataclass, field
from typing import Optional

from .indexer import Track


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
