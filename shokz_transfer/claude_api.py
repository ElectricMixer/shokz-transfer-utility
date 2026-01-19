"""Claude Code API helpers for AI-powered playlist generation.

This module provides functions for Claude Code skills to interact with
the Shokz Transfer Utility library programmatically.
"""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import load_config, Config
from .indexer import Track, load_cache, cache_exists
from .playlist import Playlist, save_session, load_session, session_exists
from .search import SearchField, search_tracks


@dataclass
class LibrarySummary:
    """Summary statistics about the music library."""
    total_tracks: int
    total_size_mb: float
    unique_artists: int
    unique_albums: int
    unique_genres: int
    top_artists: list[tuple[str, int]]  # (artist, count) pairs
    top_genres: list[tuple[str, int]]   # (genre, count) pairs
    format_breakdown: dict[str, int]    # {"mp3": count, "aac": count}


def get_library() -> Optional[list[Track]]:
    """Load the music library from cache.

    Returns:
        List of Track objects, or None if no cache exists.
    """
    if not cache_exists():
        return None
    return load_cache()


def get_library_summary(library: Optional[list[Track]] = None) -> Optional[LibrarySummary]:
    """Get summary statistics about the music library.

    Args:
        library: Optional pre-loaded library. If None, loads from cache.

    Returns:
        LibrarySummary object, or None if library unavailable.
    """
    if library is None:
        library = get_library()
    if library is None:
        return None

    # Count artists, albums, genres
    artists = Counter(t.artist for t in library)
    albums = set(t.album for t in library)
    genres = Counter(t.genre for t in library)
    formats = Counter(t.format for t in library)

    # Calculate totals
    total_size = sum(t.size_bytes for t in library) / (1024 * 1024)

    return LibrarySummary(
        total_tracks=len(library),
        total_size_mb=round(total_size, 1),
        unique_artists=len(artists),
        unique_albums=len(albums),
        unique_genres=len(genres),
        top_artists=artists.most_common(20),
        top_genres=genres.most_common(15),
        format_breakdown=dict(formats),
    )


def search_by_artist(library: list[Track], query: str) -> list[Track]:
    """Search for tracks by artist name.

    Args:
        library: The track library to search.
        query: Artist name to search for (case-insensitive substring match).

    Returns:
        List of matching tracks.
    """
    return search_tracks(library, query, SearchField.ARTIST)


def search_by_album(library: list[Track], query: str) -> list[Track]:
    """Search for tracks by album name.

    Args:
        library: The track library to search.
        query: Album name to search for (case-insensitive substring match).

    Returns:
        List of matching tracks.
    """
    return search_tracks(library, query, SearchField.ALBUM)


def search_by_title(library: list[Track], query: str) -> list[Track]:
    """Search for tracks by song title.

    Args:
        library: The track library to search.
        query: Song title to search for (case-insensitive substring match).

    Returns:
        List of matching tracks.
    """
    return search_tracks(library, query, SearchField.TITLE)


def search_by_genre(library: list[Track], query: str) -> list[Track]:
    """Search for tracks by genre.

    Args:
        library: The track library to search.
        query: Genre to search for (case-insensitive substring match).

    Returns:
        List of matching tracks.
    """
    return search_tracks(library, query, SearchField.GENRE)


def format_track_list(tracks: list[Track], show_index: bool = True) -> str:
    """Format a list of tracks as a readable string.

    Args:
        tracks: Tracks to format.
        show_index: Whether to show track numbers.

    Returns:
        Formatted string representation.
    """
    if not tracks:
        return "No tracks found."

    lines = []
    total_size = 0

    for i, track in enumerate(tracks, start=1):
        total_size += track.size_mb
        if show_index:
            lines.append(f"{i:3}. {track.title} - {track.artist} ({track.album}) [{track.size_mb:.1f} MB]")
        else:
            lines.append(f"- {track.title} - {track.artist} ({track.album}) [{track.size_mb:.1f} MB]")

    lines.append(f"\nTotal: {len(tracks)} tracks, {total_size:.1f} MB")
    return "\n".join(lines)


def get_all_by_artist(library: list[Track], artist: str) -> list[Track]:
    """Get all tracks by an artist, sorted by album then title.

    Args:
        library: The track library.
        artist: Exact artist name to match (case-insensitive).

    Returns:
        List of tracks sorted by album, then title.
    """
    tracks = [t for t in library if t.artist.lower() == artist.lower()]
    return sorted(tracks, key=lambda t: (t.album.lower(), t.title.lower()))


def get_all_from_album(library: list[Track], album: str) -> list[Track]:
    """Get all tracks from an album, sorted by title.

    Args:
        library: The track library.
        album: Exact album name to match (case-insensitive).

    Returns:
        List of tracks sorted by title.
    """
    tracks = [t for t in library if t.album.lower() == album.lower()]
    return sorted(tracks, key=lambda t: t.title.lower())


def get_all_in_genre(library: list[Track], genre: str) -> list[Track]:
    """Get all tracks in a genre, sorted by artist then title.

    Args:
        library: The track library.
        genre: Exact genre to match (case-insensitive).

    Returns:
        List of tracks sorted by artist, then title.
    """
    tracks = [t for t in library if t.genre.lower() == genre.lower()]
    return sorted(tracks, key=lambda t: (t.artist.lower(), t.title.lower()))


def create_playlist(tracks: list[Track], capacity_mb: int = 4000) -> Playlist:
    """Create a new playlist with the given tracks.

    Args:
        tracks: Tracks to add to the playlist.
        capacity_mb: Maximum capacity in MB (default: 4000 for OpenSwim).

    Returns:
        New Playlist object with tracks added.
    """
    playlist = Playlist(capacity_mb=capacity_mb)
    playlist.add_many(tracks)
    return playlist


def save_playlist_for_transfer(tracks: list[Track], capacity_mb: int = 4000) -> tuple[bool, str]:
    """Save a playlist for later transfer via CLI.

    This saves the playlist to the session file so the user can
    run the main CLI and transfer it to their Shokz.

    Args:
        tracks: Tracks to include in the playlist.
        capacity_mb: Maximum capacity in MB.

    Returns:
        Tuple of (success, message).
    """
    playlist = create_playlist(tracks, capacity_mb)

    if playlist.is_over_capacity:
        return False, f"Playlist exceeds capacity: {playlist.total_size_mb:.1f} MB > {capacity_mb} MB"

    if save_session(playlist):
        return True, f"Saved playlist: {playlist.count} tracks, {playlist.total_size_mb:.1f} MB. Run the CLI to transfer."
    else:
        return False, "Failed to save playlist session."


def get_current_playlist() -> Optional[Playlist]:
    """Load the current saved playlist session.

    Returns:
        Playlist object if session exists, None otherwise.
    """
    if not session_exists():
        return None
    return load_session()


def get_artists_list(library: list[Track]) -> list[str]:
    """Get a sorted list of all unique artists.

    Args:
        library: The track library.

    Returns:
        Sorted list of unique artist names.
    """
    return sorted(set(t.artist for t in library), key=str.lower)


def get_albums_list(library: list[Track]) -> list[str]:
    """Get a sorted list of all unique albums.

    Args:
        library: The track library.

    Returns:
        Sorted list of unique album names.
    """
    return sorted(set(t.album for t in library), key=str.lower)


def get_genres_list(library: list[Track]) -> list[str]:
    """Get a sorted list of all unique genres.

    Args:
        library: The track library.

    Returns:
        Sorted list of unique genre names.
    """
    return sorted(set(t.genre for t in library), key=str.lower)


def get_tracks_with_unknown_genre(library: list[Track]) -> list[Track]:
    """Get tracks that have missing or unknown genre metadata.

    Claude can use its world knowledge to infer genres from artist names
    for these tracks.

    Args:
        library: The track library.

    Returns:
        Tracks with empty or "Unknown" genre fields.
    """
    unknown_values = {"", "unknown", "other", "misc", "none"}
    return [t for t in library if t.genre.lower().strip() in unknown_values]


def get_tracks_by_artist_for_inference(library: list[Track], artists: list[str]) -> dict[str, list[Track]]:
    """Group tracks by artist for genre inference.

    When genre metadata is missing, Claude can use its knowledge of artists
    to infer appropriate genres. This function groups tracks by artist name
    to facilitate bulk genre inference.

    Args:
        library: The track library.
        artists: List of artist names to retrieve.

    Returns:
        Dict mapping artist names to their tracks.
    """
    result = {}
    artist_set = {a.lower() for a in artists}
    for track in library:
        if track.artist.lower() in artist_set:
            if track.artist not in result:
                result[track.artist] = []
            result[track.artist].append(track)
    return result
