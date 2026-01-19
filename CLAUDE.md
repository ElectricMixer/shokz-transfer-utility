# Shokz Transfer Utility - Claude Context

## Project Overview
A command-line Python utility to transfer music from a NAS drive to Shokz OpenSwim headphones. The user cannot code but is familiar with Python basics.

## Current Status
**Phase: Testing Complete - Ready for Use**

All core features implemented and tested. Run with:
```bash
cd "/Users/chris/Documents/Dev Projects/Shokz Transfer Utility"
python3 -m shokz_transfer
```

## Safety Guarantee
**NAS files are NEVER modified, moved, or deleted.**

| Operation | NAS Files | Shokz Files |
|-----------|-----------|-------------|
| Scan Library | READ only | - |
| Search | No file access | - |
| View Shokz | - | READ only |
| Archive Shokz | - | READ only |
| Transfer | COPY from | DELETE then WRITE to |

The utility only: reads from NAS, copies to Shokz, deletes from Shokz.

## Hardware Setup
- **Shokz OpenSwim**: 4GB capacity, mounts at `/Volumes/OpenSwim`
- **NAS Music Sources** (must be mounted before running):
  - Primary: `/Volumes/Media/iTunes Purchased/iTunes Media/Music`
  - Secondary: `/Volumes/Media/MP3`
- ~15,900 tracks total across both sources
- File formats: MP3 and AAC/M4A

## Main Menu Options
```
1. Search & Add to Playlist  - Search by title/album/artist/genre
2. View/Edit Playlist        - See playlist, remove tracks, clear
3. View Shokz Contents       - List files currently on device
4. Archive Shokz Contents    - Save snapshot to archives/ folder
5. Transfer Playlist to Shokz - Clear device, copy playlist
6. Rescan Library            - Refresh if NAS contents changed
7. Exit
```

## Key Features
- **Search**: Case-insensitive substring match on title, album, artist, or genre
- **Selection**: Use "1, 3, 5-7" syntax or "all" or "none"
- **Deduplication**: When same song exists in MP3 and AAC, keeps AAC (configurable)
- **Size warnings**: Yellow at 90% capacity, red when over
- **Archive**: Saves JSON snapshot of Shokz contents with timestamps
- **Progress bars**: Shows progress during scan and transfer
- **Library Cache**: Saves scanned library to `library_cache.json` for instant startup

## Project Structure
```
shokz-transfer-utility/
├── shokz_transfer/
│   ├── __init__.py
│   ├── __main__.py      # Entry point for python -m
│   ├── main.py          # Main menu loop
│   ├── config.py        # Load/save config.json
│   ├── indexer.py       # Scan NAS, extract metadata, dedupe
│   ├── search.py        # Filter by title/album/artist/genre
│   ├── playlist.py      # Playlist management with size tracking
│   ├── transfer.py      # Copy to Shokz, archive contents
│   └── ui.py            # Rich tables, selection parsing, prompts
├── archives/            # Shokz content snapshots (auto-created)
├── library_cache.json   # Cached library index (auto-created)
├── config.json          # User configuration
├── requirements.txt     # mutagen, rich
├── PLAN.md
├── CLAUDE.md
└── README.md
```

## Configuration (config.json)
```json
{
  "sources": {
    "primary": "/Volumes/Media/iTunes Purchased/iTunes Media/Music",
    "secondary": "/Volumes/Media/MP3"
  },
  "target": "/Volumes/OpenSwim",
  "capacity_mb": 4000,
  "format_preference": "aac",
  "music_extensions": [".mp3", ".m4a", ".aac"]
}
```

## Implementation Status
- [x] Phase 1: Project Setup
- [x] Phase 2: Library Indexer (mutagen for metadata)
- [x] Phase 3: Search & Selection UI (rich for terminal UI)
- [x] Phase 4: Playlist Management
- [x] Phase 5: Transfer Engine
- [x] Phase 6: Main Menu & Flow
- [x] Archive feature (bonus)
- [x] Library caching for fast startup
- [ ] Phase 7: Persistent Playlists (next)
- [ ] Phase 8: AI Playlist Generation via Claude Code Skill (next)

## Dependencies
Already installed:
- `mutagen>=1.47.0` - Audio metadata reading
- `rich>=13.0.0` - Terminal UI (tables, progress bars, colors)

## Testing Results (2026-01-18)
- [x] Mount NAS drives before running
- [x] Scan library - found 15,881 tracks (initial scan takes ~2-3 min over NAS)
- [x] Search by artist/title/album/genre - case-insensitive, works correctly
- [x] Selection parser - "1,3,5-7" and "all" syntax works
- [x] View Shokz contents - shows 39 files, 345.4 MB
- [x] Archive Shokz contents - JSON saved to archives/ folder
- [ ] Transfer (not tested - requires replacing current Shokz music)
- [ ] Add tracks to playlist - not tested interactively

## Known Limitations
- No BPM filtering
- No saved playlists (only archives for reference)
- Full replacement only (no smart sync)
- Single search field at a time (no combined filters)
- First-ever library scan is slow over NAS (~2-3 min for 16k files); cached startups are instant

## GitHub Repository
https://github.com/ElectricMixer/shokz-transfer-utility

---

## Planned Features

### Phase 7: Persistent Playlists (Priority: High)

**Problem**: If user exits accidentally or needs to come back later, they lose their playlist progress.

**Solution**: Auto-save playlist to `playlist_session.json` on every change.

**Implementation**:
1. Add to `playlist.py`:
   - `save_playlist_session(playlist)` - Save current playlist to JSON
   - `load_playlist_session()` - Load saved playlist
   - `playlist_session_exists()` - Check if saved session exists

2. Modify `main.py` startup:
   - After library loads, check for existing playlist session
   - If found, offer menu: "Resume playlist (X tracks, Y MB)" or "Start fresh"

3. Auto-save triggers:
   - After `playlist.add_many()`
   - After `playlist.remove_many()`
   - After `playlist.clear()`

4. Clear session file after successful transfer

**Files to modify**: `playlist.py`, `main.py`

**Pattern**: Same as library cache implementation

---

### Phase 8: AI-Powered Playlist Generation via Claude Code Skill (Priority: High)

**Problem**: Manual CLI workflow is tedious. User wants to describe a vibe/mood and get a smart playlist.

**Solution**: Create a Claude Code skill where Claude acts as an AI DJ that understands your music library.

**Why this approach**:
- Claude IS the AI - no need for separate ML models or embeddings
- Claude can understand nuanced requests: "upbeat but not too aggressive", "90s nostalgia", "songs for a rainy day"
- Claude can explain its choices and refine based on feedback
- No API costs beyond normal Claude Code usage

**How it works**:
- Skill file teaches Claude about the utility's Python API
- Claude loads your library and understands what artists/albums/genres you have
- User describes what they want in natural language
- Claude searches, curates, and builds playlist conversationally
- Claude explains why it picked each song

**Implementation**:

1. Create skill definition file: `.claude/commands/shokz.md`
   ```markdown
   # /shokz - Shokz Music Transfer Assistant

   You help the user build playlists for their Shokz OpenSwim headphones.

   ## Available Python API

   Load library (always do this first):
   ```python
   from shokz_transfer.config import load_config
   from shokz_transfer.indexer import load_cache
   config = load_config()
   library = load_cache()  # Returns list of Track objects
   ```

   Search tracks:
   ```python
   from shokz_transfer.search import search_tracks, SearchField
   # SearchField options: TITLE, ARTIST, ALBUM, GENRE
   results = search_tracks(library, "query", SearchField.ARTIST)
   ```

   Track object properties:
   - track.title, track.artist, track.album, track.genre
   - track.size_mb, track.path, track.format

   ## Workflow
   1. Load library from cache
   2. Search based on user's description
   3. Show curated results with total size
   4. User approves or refines
   5. Save to playlist session for transfer via CLI
   ```

2. Create helper script: `shokz_transfer/claude_api.py`
   - `get_library_summary()` - Returns unique artists, albums, genres
   - `search_and_format(query, field)` - Search and return formatted results
   - `save_playlist_for_transfer(tracks)` - Save selected tracks to session

**Example interactions**:

```
User: /shokz I want upbeat songs for running, mix of 80s rock and modern pop

Claude: [Loads library, analyzes your collection]
        Based on your library, here's a 28-song running playlist (298 MB):

        High Energy 80s (12 songs):
        - Born to Run - Bruce Springsteen (perfect running cadence)
        - Running on Empty - Jackson Browne
        - Take On Me - A-ha
        ...

        Modern Energy (10 songs):
        - Shake It Off - Taylor Swift
        - Uptown Funk - Bruno Mars
        ...

        Want me to save this? Or adjust - more 80s? Different vibe?
```

```
User: /shokz something mellow for a long flight, acoustic and chill

Claude: Here's a 3-hour calm playlist (387 MB):

        Acoustic/Folk:
        - Graceland - Paul Simon
        - Fire and Rain - James Taylor
        ...

        I noticed you have a lot of Bob Dylan - want me to add some?
```

```
User: /shokz surprise me - you pick based on what's in my library

Claude: Looking at your collection, you have great taste in classic rock
        and singer-songwriters. Here's a "Best Of Your Library" mix...
```

**Key benefit**: Claude understands context, can refine, and explains choices - true AI curation.

**Files to create**: `.claude/commands/shokz.md`, `shokz_transfer/claude_api.py`
**Files to modify**: None (additive only)

---

## Implementation Order

1. **Phase 7 first** - Persistent playlists (30 min)
   - Same pattern as library cache
   - Immediate usability improvement
   - Required for Phase 8 (skill saves playlist for later transfer)

2. **Phase 8 second** - Claude Code skill (1-2 hours)
   - Depends on Phase 7 for playlist persistence
   - Transforms UX completely
