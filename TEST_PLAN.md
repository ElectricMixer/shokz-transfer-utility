# Test Plan: Phase 7 & 8 Features

## Prerequisites
- NAS drives mounted at `/Volumes/Media/...`
- Library cache exists (run CLI once to scan if needed)
- Shokz NOT required for playlist tests (only for transfer)

---

## Phase 7: Persistent Playlists

### Test 1: Auto-Save on Add
1. Start CLI: `python3 -m shokz_transfer`
2. Choose "Use cached library"
3. If prompted about existing playlist, choose "Start fresh"
4. Search & Add: Search for an artist, select a few tracks
5. **Exit the CLI** (option 7 or Ctrl+C)
6. Check file exists: `ls -la playlist_session.json`
7. View contents: `cat playlist_session.json`

**Expected**: JSON file contains saved tracks with metadata

### Test 2: Resume Playlist on Restart
1. Start CLI again: `python3 -m shokz_transfer`
2. Should see prompt: "Found saved playlist: X tracks, Y MB"
3. Choose "Resume playlist"

**Expected**: Playlist restored with same tracks from Test 1

### Test 3: Start Fresh Option
1. Exit and restart CLI
2. Choose "Start fresh (discard saved playlist)"

**Expected**: Empty playlist, session file deleted

### Test 4: Auto-Save on Remove
1. Add some tracks to playlist
2. View/Edit Playlist → Remove tracks (e.g., "1,2")
3. Exit CLI
4. Restart CLI and resume

**Expected**: Removed tracks stay removed after restart

### Test 5: Clear Playlist Clears Session
1. Add tracks to playlist
2. View/Edit Playlist → Clear all → confirm "y"
3. Exit CLI
4. Check: `ls playlist_session.json`

**Expected**: Session file deleted (or prompt says "Start fresh" on restart)

### Test 6: Session Cleared After Transfer
*(Only if willing to replace Shokz music)*
1. Build a small playlist
2. Connect Shokz
3. Transfer Playlist to Shokz
4. After success, exit and restart CLI

**Expected**: No resume prompt (session was cleared)

---

## Phase 8: AI Playlist Generation

### Test 7: Skill Loads Library
1. In Claude Code, run: `/shokz`
2. Say: "What's in my library?"

**Expected**: Claude loads library, shows summary (track count, top artists, genres)

### Test 8: Search by Genre
1. `/shokz give me some rock music`

**Expected**: Claude searches genre tags AND known rock artists, presents curated list

### Test 9: Genre Inference from Artist
1. `/shokz I want jazz`
2. Check if Claude finds jazz artists even if genre tags are missing

**Expected**: Claude uses artist knowledge (Miles Davis, Coltrane, etc.) not just genre tags

### Test 10: Workout Playlist
1. `/shokz high energy music for working out`

**Expected**: Claude builds energetic playlist, explains choices, shows total size

### Test 11: Save Playlist for Transfer
1. After Claude presents a playlist, say "save it"
2. Check: `cat playlist_session.json`

**Expected**: Playlist saved to session file

### Test 12: Launch Manual CLI from Skill
1. `/shokz I want to build it myself`

**Expected**: Claude launches the CLI for manual playlist building

### Test 13: Refine Playlist
1. `/shokz chill acoustic music`
2. After Claude presents playlist, say "add more folk" or "remove the pop songs"

**Expected**: Claude refines the playlist based on feedback

### Test 14: Size Awareness
1. `/shokz give me everything by [large artist in your library]`
2. If over 4GB, Claude should warn

**Expected**: Claude shows total size, warns if over 4000 MB capacity

---

## Quick Smoke Test (5 minutes)

Run these in sequence to verify core functionality:

```bash
# 1. Check Python syntax
cd "/Users/chris/Documents/Dev Projects/Shokz Transfer Utility"
python3 -m py_compile shokz_transfer/playlist.py shokz_transfer/main.py shokz_transfer/claude_api.py

# 2. Check imports
python3 -c "from shokz_transfer.playlist import save_session, load_session; print('OK')"
python3 -c "from shokz_transfer.claude_api import get_library, save_playlist_for_transfer; print('OK')"

# 3. Quick CLI test (manual)
python3 -m shokz_transfer
# → Use cache, search for artist, add 2 tracks, exit
# → Restart, verify resume prompt works
```

---

## Test Results

| Test | Status | Notes |
|------|--------|-------|
| 1. Auto-Save on Add | | |
| 2. Resume on Restart | | |
| 3. Start Fresh Option | | |
| 4. Auto-Save on Remove | | |
| 5. Clear Clears Session | | |
| 6. Transfer Clears Session | | |
| 7. Skill Loads Library | | |
| 8. Search by Genre | | |
| 9. Genre Inference | | |
| 10. Workout Playlist | | |
| 11. Save for Transfer | | |
| 12. Launch Manual CLI | | |
| 13. Refine Playlist | | |
| 14. Size Awareness | | |
