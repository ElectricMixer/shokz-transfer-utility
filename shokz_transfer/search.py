"""Search and filter logic for music library."""

from enum import Enum
from typing import Callable

from .indexer import Track


class SearchField(Enum):
    """Fields that can be searched."""

    TITLE = "title"
    ALBUM = "album"
    ARTIST = "artist"
    GENRE = "genre"


def search_tracks(
    tracks: list[Track],
    query: str,
    field: SearchField,
) -> list[Track]:
    """Search tracks by a specific field.

    Args:
        tracks: List of tracks to search.
        query: Search query (case-insensitive substring match).
        field: Which field to search.

    Returns:
        List of matching tracks.
    """
    query_lower = query.lower().strip()

    if not query_lower:
        return []

    # Get the appropriate field getter
    field_getters: dict[SearchField, Callable[[Track], str]] = {
        SearchField.TITLE: lambda t: t.title,
        SearchField.ALBUM: lambda t: t.album,
        SearchField.ARTIST: lambda t: t.artist,
        SearchField.GENRE: lambda t: t.genre,
    }

    getter = field_getters[field]

    return [
        track
        for track in tracks
        if query_lower in getter(track).lower()
    ]


def search_by_title(tracks: list[Track], query: str) -> list[Track]:
    """Search tracks by title."""
    return search_tracks(tracks, query, SearchField.TITLE)


def search_by_album(tracks: list[Track], query: str) -> list[Track]:
    """Search tracks by album."""
    return search_tracks(tracks, query, SearchField.ALBUM)


def search_by_artist(tracks: list[Track], query: str) -> list[Track]:
    """Search tracks by artist."""
    return search_tracks(tracks, query, SearchField.ARTIST)


def search_by_genre(tracks: list[Track], query: str) -> list[Track]:
    """Search tracks by genre."""
    return search_tracks(tracks, query, SearchField.GENRE)
