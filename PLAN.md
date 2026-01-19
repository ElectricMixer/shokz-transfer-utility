# Shokz Transfer Utility - Implementation Plan

## Overview
A command-line utility to simplify transferring music from a NAS drive to Shokz OpenSwim headphones. The tool provides interactive search and filtering, playlist building, and one-click transfer with progress feedback.

## Technical Stack
- **Language**: Python 3
- **Key Libraries**:
  - `mutagen` - Reading MP3/AAC metadata (artist, album, genre, title)
  - `rich` - Terminal UI (progress bars, tables, interactive selection)
  - `pathlib` - Cross-platform path handling

## Source Configuration
- **Primary Source**: `/Volumes/Media/iTunes Purchased/iTunes Media/Music`
- **Secondary Source**: `/Volumes/Media/MP3`
- **Target**: `/Volumes/OpenSwim`
- **Capacity**: 4GB

## Core Features

### 1. Music Library Indexing
- Scan both source directories for MP3 and AAC/M4A files
- Extract metadata: title, artist, album, genre, file size, format
- Build an in-memory index for fast searching
- Handle missing metadata gracefully (use filename as fallback)

### 2. Interactive Search & Filter
- Filter by: song title, album, artist, or genre
- Display results as a numbered list
- Allow selection via comma-separated numbers and ranges (e.g., "1, 3, 5-7")
- Show file size alongside each result

### 3. Playlist Management
- Add multiple search results to a running playlist
- Display current playlist with cumulative size
- Show warning when approaching 4GB limit
- Allow removal of items from playlist
- Clear playlist option

### 4. Transfer Engine
- Validate Shokz is mounted at `/Volumes/OpenSwim`
- Clear existing music files from Shokz (preserve system files)
- Copy selected files with progress indicator
- Show files copied count and space used/remaining
- Verify transfer completed successfully

### 5. Format Preference
- Configurable preference: AAC (smaller) or MP3
- When duplicate songs exist in both formats, prefer selected format
- Store preference in config file

### 6. Headphone Content Reader (v1 bonus)
- List current files on Shokz OpenSwim
- Show total space used

---

## File Structure
```
shokz-transfer/
├── shokz_transfer/
│   ├── __init__.py
│   ├── main.py           # Entry point, main menu loop
│   ├── config.py         # Configuration management
│   ├── indexer.py        # Library scanning and indexing
│   ├── search.py         # Search and filter logic
│   ├── playlist.py       # Playlist management
│   ├── transfer.py       # File transfer operations
│   └── ui.py             # Terminal UI helpers (tables, selection)
├── config.json           # User preferences
├── requirements.txt
└── README.md
```

---

## Implementation Steps

### Phase 1: Project Setup
- [ ] Initialize Python project structure
- [ ] Create requirements.txt with dependencies
- [ ] Set up configuration file with source paths and preferences

### Phase 2: Library Indexer
- [ ] Implement directory scanner for MP3/AAC files
- [ ] Extract metadata using mutagen
- [ ] Build searchable index with deduplication logic
- [ ] Handle format preference (AAC vs MP3)

### Phase 3: Search & Selection UI
- [ ] Implement search by song, album, artist, genre
- [ ] Display results as numbered list with size info
- [ ] Parse selection input (numbers, ranges)
- [ ] Handle empty results gracefully

### Phase 4: Playlist Management
- [ ] Create playlist data structure
- [ ] Add selected tracks to playlist
- [ ] Display playlist with running total size
- [ ] Warn when exceeding 4GB limit
- [ ] Allow track removal and playlist clearing

### Phase 5: Transfer Engine
- [ ] Check Shokz mount status
- [ ] Identify and clear existing music files (safe delete)
- [ ] Copy files with progress bar
- [ ] Report transfer summary

### Phase 6: Main Menu & Flow
- [ ] Create main interactive menu
- [ ] Implement session flow:
  1. Scan library (with progress)
  2. Search/filter loop
  3. Build playlist
  4. Review and transfer
- [ ] Add "view Shokz contents" option

### Phase 7: Polish & Error Handling
- [ ] Handle NAS not mounted
- [ ] Handle Shokz not connected
- [ ] Handle interrupted transfers
- [ ] Add helpful error messages

---

## Interactive Flow (User Experience)

```
$ python -m shokz_transfer

🎧 Shokz Transfer Utility
========================

Scanning music library...
Found 2,147 tracks in 45 seconds

Main Menu:
1. Search & Add to Playlist
2. View Current Playlist (0 tracks, 0 MB)
3. View Shokz Contents
4. Transfer Playlist to Shokz
5. Settings
6. Exit

> 1

Search by:
1. Song Title
2. Album
3. Artist
4. Genre

> 3

Enter artist name: Daft Punk

Found 24 tracks:

 #  │ Title                    │ Album              │ Size
────┼──────────────────────────┼────────────────────┼──────
 1  │ Get Lucky                │ Random Access...   │ 8.2 MB
 2  │ Instant Crush            │ Random Access...   │ 9.1 MB
 3  │ Lose Yourself to Dance   │ Random Access...   │ 7.8 MB
...

Select tracks (e.g., 1,3,5-7) or 'all' or 'none': 1-3, 5

Added 4 tracks (33.2 MB) to playlist.
Current playlist: 4 tracks, 33.2 MB / 4,000 MB

[Press Enter to continue]
```

---

## Configuration File (config.json)

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

---

## Dependencies (requirements.txt)

```
mutagen>=1.47.0
rich>=13.0.0
```

---

## Completed (as of 2026-01-18)
- [x] All phases 1-6 implemented and tested
- [x] Archive feature added (save Shokz contents to JSON)
- [x] Library caching added (instant startup after first scan)
- [x] 15,881 tracks indexed from NAS

## Notes
- BPM filtering deferred to future version
- Smart sync (instead of full replace) deferred to future version

---

## Next Features (Planned)

### Phase 7: Persistent Playlists
**Status**: Ready to implement

Auto-save playlist state so users can resume after exiting.

See CLAUDE.md for full implementation details.

### Phase 8: AI-Powered Playlist Generation
**Status**: Ready to implement (after Phase 7)

Create a `/shokz` skill for Claude Code where Claude acts as an AI DJ:
- Understands your entire music library (artists, albums, genres)
- Accepts natural language requests: "mellow acoustic for a long flight", "80s workout mix"
- Curates intelligent playlists based on vibe, mood, activity
- Explains choices and refines based on feedback
- No external APIs or ML models needed - Claude IS the AI

Example: "surprise me with the best of my library" → Claude analyzes your collection and builds a personalized mix

See CLAUDE.md for full implementation details.
