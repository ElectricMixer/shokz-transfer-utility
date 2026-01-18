# Shokz Transfer Utility - Claude Context

## Project Overview
A command-line Python utility to transfer music from a NAS drive to Shokz OpenSwim headphones. The user cannot code but is familiar with Python basics.

## Current Status
**Phase: Project Setup Complete - Ready to Implement**

The project structure and plan are in place. No functional code has been written yet. Next step is to implement Phase 2 (Library Indexer) from PLAN.md.

## Hardware Setup
- **Shokz OpenSwim**: 4GB capacity, mounts at `/Volumes/OpenSwim`
- **NAS Music Sources**:
  - Primary: `/Volumes/Media/iTunes Purchased/iTunes Media/Music`
  - Secondary: `/Volumes/Media/MP3`
- ~2,000 tracks total across both sources
- File formats: MP3 and AAC/M4A

## Key Requirements
1. **Search/Filter**: By song title, album, artist, or genre (one filter at a time)
2. **Selection UI**: Numbered list like Claude Code, select with "1, 3, 5-7" syntax
3. **Playlist Building**: Add multiple searches before transferring
4. **Size Management**: Warn if playlist exceeds 4GB, let user pick what to remove
5. **Format Preference**: Prefer AAC over MP3 when duplicates exist (configurable)
6. **Transfer**: Complete replacement of music files on Shokz (preserve system files)
7. **Progress**: Show files copied and space used during transfer
8. **View Contents**: Ability to see what's currently on the Shokz

## Implementation Order (from PLAN.md)
- [x] Phase 1: Project Setup
- [ ] Phase 2: Library Indexer (mutagen for metadata)
- [ ] Phase 3: Search & Selection UI (rich for terminal UI)
- [ ] Phase 4: Playlist Management
- [ ] Phase 5: Transfer Engine
- [ ] Phase 6: Main Menu & Flow
- [ ] Phase 7: Error Handling Polish

## Files to Implement
| File | Purpose | Status |
|------|---------|--------|
| `shokz_transfer/config.py` | Load/save config.json | Stub only |
| `shokz_transfer/indexer.py` | Scan dirs, extract metadata, build index | Stub only |
| `shokz_transfer/search.py` | Filter library by song/album/artist/genre | Stub only |
| `shokz_transfer/playlist.py` | Track selection, size totals, warnings | Stub only |
| `shokz_transfer/transfer.py` | Clear Shokz, copy files, progress | Stub only |
| `shokz_transfer/ui.py` | Tables, numbered selection, prompts | Stub only |
| `shokz_transfer/main.py` | Main menu loop, session flow | Stub only |

## Technical Decisions Made
- Python with `mutagen` (metadata) and `rich` (terminal UI)
- Config stored in `config.json` in project root
- No BPM filtering (deferred)
- No playlist persistence (deferred)
- No smart sync - full replacement only (deferred)

## GitHub Repository
https://github.com/ElectricMixer/shokz-transfer-utility
