# Shokz Transfer Utility

A command-line utility to simplify transferring music from a NAS drive to Shokz OpenSwim headphones.

## Features

- **Interactive Search**: Search your music library by song title, album, artist, or genre
- **Playlist Building**: Build a playlist across multiple searches with running size totals
- **Smart Deduplication**: When songs exist in multiple formats, prefer your chosen format (AAC or MP3)
- **Size Management**: Warns before exceeding the 4GB Shokz capacity
- **One-Click Transfer**: Transfer your playlist with progress feedback
- **Headphone Reader**: View what's currently on your Shokz

## Requirements

- Python 3.8+
- macOS (tested on macOS)
- Shokz OpenSwim headphones connected via USB

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ElectricMixer/shokz-transfer-utility.git
   cd shokz-transfer-utility
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Edit `config.json` to match your music library paths:
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

## Usage

```bash
python -m shokz_transfer
```

### Workflow

1. **Scan**: The utility scans your music library on startup
2. **Search**: Search by song, album, artist, or genre
3. **Select**: Pick tracks from numbered results (e.g., `1, 3, 5-7` or `all`)
4. **Build**: Add multiple searches to your playlist
5. **Review**: Check playlist size against 4GB limit
6. **Transfer**: One-click transfer to your Shokz

## Configuration Options

| Option | Description |
|--------|-------------|
| `sources.primary` | Primary music folder (searched first) |
| `sources.secondary` | Secondary music folder (fallback) |
| `target` | Shokz mount path |
| `capacity_mb` | Device capacity in MB (default: 4000) |
| `format_preference` | Preferred format: `aac` or `mp3` |
| `music_extensions` | File extensions to include |

## License

MIT
