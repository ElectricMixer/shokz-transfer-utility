# Shokz Transfer Utility - Claude Context

## Project Overview
A command-line Python utility to transfer music from a NAS drive to Shokz OpenSwim headphones. The user cannot code but is familiar with Python basics.

## Current Status
**Phase: All Features Complete - Ready for Use**

All core features plus AI playlist generation implemented. Run with:
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
- **Persistent Playlists**: Auto-saves playlist to `playlist_session.json`, resume on restart
- **AI Playlist Generation**: Use `/shokz` skill for natural language playlist creation

## Project Structure
```
shokz-transfer-utility/
├── .claude/
│   └── commands/
│       └── shokz.md     # AI playlist skill for Claude Code
├── shokz_transfer/
│   ├── __init__.py
│   ├── __main__.py      # Entry point for python -m
│   ├── main.py          # Main menu loop
│   ├── config.py        # Load/save config.json
│   ├── indexer.py       # Scan NAS, extract metadata, dedupe
│   ├── search.py        # Filter by title/album/artist/genre
│   ├── playlist.py      # Playlist management with session persistence
│   ├── transfer.py      # Copy to Shokz, archive contents
│   ├── claude_api.py    # API helpers for AI playlist generation
│   └── ui.py            # Rich tables, selection parsing, prompts
├── archives/            # Shokz content snapshots (auto-created)
├── library_cache.json   # Cached library index (auto-created)
├── playlist_session.json # Saved playlist (auto-created)
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
- [x] Phase 7: Persistent Playlists
- [x] Phase 8: AI Playlist Generation via Claude Code Skill

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
- Full replacement only (no smart sync)
- Single search field at a time (no combined filters)
- First-ever library scan is slow over NAS (~2-3 min for 16k files); cached startups are instant

## GitHub Repository
https://github.com/ElectricMixer/shokz-transfer-utility

---

## AI Playlist Generation (/shokz skill)

Use the `/shokz` command in Claude Code to build playlists with natural language:

```
/shokz high energy music for working out
/shokz chill acoustic for relaxing
/shokz 80s classics mix
/shokz surprise me with your picks
```

Claude will:
1. Load your library and analyze your collection
2. Search and curate tracks matching your request
3. **Infer genres from artist names** when metadata is missing (e.g., knows The Beatles = Rock)
4. Present the playlist with explanations
5. Refine based on feedback
6. Save to `playlist_session.json` for transfer via CLI

After Claude saves the playlist, run the CLI and select "Transfer Playlist to Shokz".

---

## Persistent Playlists

Playlists are automatically saved to `playlist_session.json`:
- **Auto-saves** after adding/removing tracks
- **Resume on restart** - prompted to resume or start fresh
- **Cleared after transfer** - fresh start for next playlist

This means you can:
- Build a playlist over multiple sessions
- Exit accidentally without losing progress
- Use `/shokz` skill to build playlist, then transfer via CLI later
