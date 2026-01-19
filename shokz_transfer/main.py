"""Main entry point for Shokz Transfer Utility."""

from rich.console import Console
from rich.table import Table

from .config import load_config, Config
from .indexer import (
    Track,
    build_index,
    IndexResult,
    cache_exists,
    get_cache_info,
    load_cache,
    save_cache,
)
from .search import SearchField, search_tracks
from .playlist import (
    Playlist,
    session_exists,
    get_session_info,
    load_session,
    save_session,
    clear_session,
)
from .transfer import (
    is_shokz_mounted,
    get_shokz_contents,
    get_shokz_usage,
    perform_full_transfer,
    archive_shokz_contents,
)
from .ui import (
    console,
    display_tracks,
    display_playlist,
    parse_selection,
    prompt_menu,
    prompt_input,
    print_success,
    print_error,
    print_warning,
    print_info,
    create_progress,
)

# Application state
library: list[Track] = []
playlist: Playlist
config: Config


def scan_library(save_to_cache: bool = True) -> bool:
    """Scan the music library with progress display.

    Args:
        save_to_cache: If True, save the scanned library to cache file.

    Returns True if tracks were found, False otherwise.
    """
    global library

    console.print("\n[bold]Scanning music library...[/bold]")

    with create_progress() as progress:
        task = progress.add_task("Scanning...", total=None)

        def on_progress(status: str, current: int, total: int) -> None:
            if total > 0:
                progress.update(task, total=total, completed=current, description=status)
            else:
                progress.update(task, description=status)

        result = build_index(config, on_progress)

    # Report any errors encountered
    if result.has_errors:
        console.print()
        for error in result.errors:
            if error.error_type == "permission_denied":
                print_error(error.message)
            else:
                print_warning(error.message)

    library = result.tracks
    print_success(f"Found {len(library)} tracks")

    # Save to cache if requested and tracks were found
    if save_to_cache and len(library) > 0:
        save_cache(library)
        print_info("Library cached for faster startup next time.")

    return len(library) > 0


def load_library_from_cache() -> bool:
    """Load the library from cache file.

    Returns True if cache was loaded successfully, False otherwise.
    """
    global library

    console.print("\n[bold]Loading library from cache...[/bold]")

    cached_tracks = load_cache()
    if cached_tracks is None:
        print_error("Failed to load cache.")
        return False

    library = cached_tracks
    print_success(f"Loaded {len(library)} tracks from cache")
    return True


def startup_library_choice() -> bool:
    """Handle startup library loading with cache option.

    Returns True if library was loaded successfully, False otherwise.
    """
    # Check if cache exists
    if cache_exists():
        cache_info = get_cache_info()
        if cache_info:
            # Parse and format the date
            cached_at = cache_info["cached_at"]
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(cached_at)
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                date_str = cached_at

            console.print()
            console.print(f"[dim]Found cached library: {cache_info['track_count']} tracks from {date_str}[/dim]")

            choice = prompt_menu(
                "Library Options:",
                [
                    f"Use cached library ({cache_info['track_count']} tracks) - Fast",
                    "Rescan NAS library - Slow but gets latest changes",
                ],
            )

            if choice == 0:
                return load_library_from_cache()
            elif choice == 1:
                return scan_library(save_to_cache=True)
            else:
                # User cancelled
                return False

    # No cache exists, must scan
    return scan_library(save_to_cache=True)


def startup_playlist_session() -> bool:
    """Check for and optionally resume a saved playlist session.

    Returns True if a session was loaded, False otherwise.
    """
    global playlist

    if not session_exists():
        return False

    info = get_session_info()
    if not info:
        return False

    # Parse and format the date
    saved_at = info["saved_at"]
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(saved_at)
        date_str = dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        date_str = saved_at

    console.print()
    console.print(f"[dim]Found saved playlist: {info['track_count']} tracks, {info['total_size_mb']:.1f} MB from {date_str}[/dim]")

    choice = prompt_menu(
        "Playlist Session:",
        [
            f"Resume playlist ({info['track_count']} tracks, {info['total_size_mb']:.1f} MB)",
            "Start fresh (discard saved playlist)",
        ],
    )

    if choice == 0:
        loaded_playlist = load_session()
        if loaded_playlist:
            playlist = loaded_playlist
            print_success(f"Resumed playlist: {playlist.count} tracks, {playlist.total_size_mb:.1f} MB")
            return True
        else:
            print_warning("Failed to load saved playlist. Starting fresh.")
            clear_session()
            return False
    elif choice == 1:
        clear_session()
        print_info("Starting with empty playlist.")
        return False

    return False


def search_and_add() -> None:
    """Search for tracks and add selection to playlist."""
    # Choose search field
    choice = prompt_menu(
        "Search by:",
        ["Song Title", "Album", "Artist", "Genre", "Back to Main Menu"],
    )

    if choice == -1 or choice == 4:
        return

    field_map = {
        0: (SearchField.TITLE, "song title"),
        1: (SearchField.ALBUM, "album"),
        2: (SearchField.ARTIST, "artist"),
        3: (SearchField.GENRE, "genre"),
    }

    field, field_name = field_map[choice]
    query = prompt_input(f"Enter {field_name}:")

    if not query:
        print_warning("No search term entered.")
        return

    # Search
    results = search_tracks(library, query, field)

    if not results:
        print_warning(f"No tracks found matching '{query}'")
        return

    # Display results
    console.print()
    display_tracks(results, f"Results for '{query}'")

    # Prompt for selection
    console.print()
    console.print("[dim]Select tracks (e.g., 1,3,5-7) or 'all' or 'none':[/dim]")
    user_input = console.input("[cyan]> [/cyan]")

    indices = parse_selection(user_input, len(results))

    if not indices:
        print_info("No tracks selected.")
        return

    # Add to playlist
    selected = [results[i] for i in indices]
    added = playlist.add_many(selected)

    if added > 0:
        total_mb = sum(results[i].size_mb for i in indices)
        print_success(f"Added {added} tracks ({total_mb:.1f} MB) to playlist.")
        console.print(f"[dim]{playlist.get_status_message()}[/dim]")

        # Auto-save playlist session
        save_session(playlist)

        if playlist.is_over_capacity:
            print_warning("Playlist exceeds Shokz capacity! Remove some tracks before transferring.")
    else:
        print_info("Selected tracks were already in playlist.")


def view_playlist() -> None:
    """View and manage the current playlist."""
    if playlist.count == 0:
        print_warning("Playlist is empty.")
        return

    while True:
        console.print()
        display_playlist(playlist.tracks, config.capacity_mb)

        choice = prompt_menu(
            "Playlist Options:",
            ["Remove tracks", "Clear all", "Back to Main Menu"],
        )

        if choice == -1 or choice == 2:
            return

        if choice == 0:
            # Remove tracks
            console.print("[dim]Select tracks to remove (e.g., 1,3,5-7):[/dim]")
            user_input = console.input("[cyan]> [/cyan]")
            indices = parse_selection(user_input, playlist.count)

            if indices:
                removed = playlist.remove_many(indices)
                print_success(f"Removed {len(removed)} tracks.")
                # Auto-save playlist session
                if playlist.count > 0:
                    save_session(playlist)
                else:
                    clear_session()
            else:
                print_info("No tracks removed.")

        elif choice == 1:
            # Clear all
            console.print("[yellow]Clear entire playlist? (y/n)[/yellow]")
            confirm = console.input("[cyan]> [/cyan]").strip().lower()

            if confirm == "y":
                count = playlist.clear()
                print_success(f"Cleared {count} tracks from playlist.")
                # Clear session file
                clear_session()
                return


def view_shokz_contents() -> None:
    """View what's currently on the Shokz device."""
    if not is_shokz_mounted(config.target):
        print_error(f"Shokz not connected at {config.target}")
        return

    files = get_shokz_contents(config.target, config.music_extensions)

    if not files:
        print_info("No music files on Shokz.")
        return

    total_mb, count = get_shokz_usage(config.target, config.music_extensions)

    table = Table(title="Shokz Contents")
    table.add_column("#", justify="right", style="cyan", width=4)
    table.add_column("Filename", style="white")
    table.add_column("Size", justify="right", style="magenta", width=10)

    for i, f in enumerate(files, start=1):
        table.add_row(str(i), f.name, f"{f.size_mb:.1f} MB")

    console.print()
    console.print(table)
    console.print(f"[dim]{count} files, {total_mb:.1f} MB / {config.capacity_mb} MB[/dim]")


def archive_shokz() -> None:
    """Archive current Shokz contents to a JSON file."""
    if not is_shokz_mounted(config.target):
        print_error(f"Shokz not connected at {config.target}")
        return

    total_mb, count = get_shokz_usage(config.target, config.music_extensions)

    if count == 0:
        print_warning("No music files on Shokz to archive.")
        return

    console.print(f"\n[dim]Archiving {count} files ({total_mb:.1f} MB)...[/dim]")

    success, result = archive_shokz_contents(config)

    if success:
        print_success(f"Archive saved to: {result}")
    else:
        print_error(result)


def transfer_playlist() -> None:
    """Transfer the playlist to Shokz."""
    if playlist.count == 0:
        print_warning("Playlist is empty. Add some tracks first.")
        return

    if not is_shokz_mounted(config.target):
        print_error(f"Shokz not connected at {config.target}")
        return

    if playlist.is_over_capacity:
        print_error("Playlist exceeds Shokz capacity! Remove some tracks first.")
        return

    # Show summary and confirm
    console.print()
    console.print("[bold]Transfer Summary[/bold]")
    console.print(f"  Tracks: {playlist.count}")
    console.print(f"  Size: {playlist.total_size_mb:.1f} MB / {config.capacity_mb} MB")
    console.print()
    console.print("[yellow]This will REPLACE all music on your Shokz.[/yellow]")
    console.print("[yellow]Continue? (y/n)[/yellow]")

    confirm = console.input("[cyan]> [/cyan]").strip().lower()

    if confirm != "y":
        print_info("Transfer cancelled.")
        return

    # Perform transfer
    console.print()

    with create_progress() as progress:
        task = progress.add_task("Transferring...", total=playlist.count)

        def on_progress(name: str, current: int, total: int) -> None:
            progress.update(task, completed=current, description=f"Copying: {name[:30]}")

        result = perform_full_transfer(
            playlist.tracks,
            config,
            progress_callback=on_progress,
        )

    console.print()

    if result.success:
        print_success(f"Transfer complete! {result.files_copied} files ({result.mb_copied:.1f} MB)")
        # Clear session after successful transfer
        clear_session()
        # Clear the playlist in memory
        playlist.clear()
    else:
        print_error("Transfer failed:")
        for error in result.errors:
            console.print(f"  [red]- {error}[/red]")


def show_main_menu() -> int:
    """Display main menu and return choice."""
    # Build menu with dynamic playlist info
    playlist_info = f"({playlist.count} tracks, {playlist.total_size_mb:.1f} MB)"

    options = [
        "Search & Add to Playlist",
        f"View/Edit Playlist {playlist_info}",
        "View Shokz Contents",
        "Archive Shokz Contents",
        "Transfer Playlist to Shokz",
        "Rescan Library",
        "Exit",
    ]

    return prompt_menu("Main Menu:", options)


def main() -> None:
    """Run the Shokz Transfer Utility."""
    global config, playlist

    # Header
    console.print()
    console.print("[bold blue]🎧 Shokz Transfer Utility[/bold blue]")
    console.print("[dim]Transfer music from NAS to Shokz OpenSwim[/dim]")

    # Load config
    try:
        config = load_config()
    except FileNotFoundError:
        print_error("Config file not found. Please create config.json")
        return
    except Exception as e:
        print_error(f"Failed to load config: {e}")
        return

    # Initialize playlist
    playlist = Playlist(capacity_mb=config.capacity_mb)

    # Load library (from cache or fresh scan)
    if not startup_library_choice():
        return

    # Check for saved playlist session
    startup_playlist_session()

    # Main menu loop
    while True:
        console.print()
        choice = show_main_menu()

        if choice == 0:
            search_and_add()
        elif choice == 1:
            view_playlist()
        elif choice == 2:
            view_shokz_contents()
        elif choice == 3:
            archive_shokz()
        elif choice == 4:
            transfer_playlist()
        elif choice == 5:
            scan_library()
        elif choice == 6 or choice == -1:
            console.print()
            print_info("Goodbye!")
            break


if __name__ == "__main__":
    main()
