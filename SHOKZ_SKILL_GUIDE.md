# Using /shokz - AI Playlist Assistant

The `/shokz` skill lets you build playlists for your Shokz OpenSwim using natural language. Just describe what you want and Claude will curate tracks from your library.

## Getting Started

1. Open Claude Code in the project directory
2. Type `/shokz` followed by what kind of music you want

## Example Requests

### By Activity
```
/shokz high energy music for working out
/shokz songs for running
/shokz relaxing music for a long flight
/shokz background music for working
```

### By Mood
```
/shokz upbeat happy songs
/shokz mellow chill vibes
/shokz something energetic but not too aggressive
```

### By Genre
```
/shokz give me some jazz
/shokz classic rock mix
/shokz 80s hits
/shokz folk and acoustic
```

### By Artist
```
/shokz everything by The Beatles
/shokz mix of Dylan and Springsteen
/shokz similar artists to Wilco
```

### Surprise Me
```
/shokz surprise me with your picks
/shokz best of my library
/shokz something I haven't listened to in a while
```

## What Claude Does

1. **Loads your library** (15,881 tracks from your NAS)
2. **Searches** by genre, artist, album, or title
3. **Infers genres** from artist names when metadata is missing
4. **Curates** a playlist that fits the 4GB Shokz capacity
5. **Explains** why each track was picked
6. **Refines** based on your feedback

## Refining Your Playlist

After Claude presents a playlist, you can say:

- "Add more 80s songs"
- "Remove the pop tracks"
- "Make it longer"
- "Too mellow, I need more energy"
- "Perfect, save it"

## Saving & Transferring

When you're happy with the playlist:

1. Say **"save it"** - Claude saves to `playlist_session.json`
2. Run the CLI: `python3 -m shokz_transfer`
3. Choose **"Resume playlist"** when prompted
4. Select **"Transfer Playlist to Shokz"**

Or say **"save it and open the CLI"** to do both at once.

## Switch to Manual Mode

If you'd rather build the playlist yourself:

```
/shokz I want to build it myself
```

Claude will launch the CLI for manual playlist building.

## Tips

- **Be specific**: "upbeat rock for running" works better than just "music"
- **Mention size**: "give me about 2 hours of music" or "fill up my Shokz"
- **Combine styles**: "mix of jazz and soul from the 60s and 70s"
- **Ask questions**: "what genres do I have?" or "who are my top artists?"

## Capacity

The Shokz OpenSwim has 4GB capacity (~4000 MB). Claude will:
- Show total playlist size
- Warn if you're over capacity
- Help trim if needed

## Quick Reference

| You Say | Claude Does |
|---------|-------------|
| `/shokz workout music` | Builds high-energy playlist |
| "add more rock" | Adds rock tracks to playlist |
| "remove track 3" | Removes specific track |
| "save it" | Saves to session file |
| "open the CLI" | Launches manual interface |
| "what's in my library?" | Shows library summary |
