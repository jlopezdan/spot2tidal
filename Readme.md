# Spotify to Tidal Playlist Transfer

A Python script that transfers playlists from Spotify to Tidal, including all track information and metadata.

## Features

- 🎵 **Complete Playlist Transfer**: Transfers playlist name, description, and all tracks
- 🔍 **Smart Track Matching**: Uses ISRC codes and fuzzy matching to find tracks on Tidal
- 📊 **Detailed Reporting**: Shows transfer success rate and missing tracks
- 🔐 **Secure Authentication**: OAuth2 for both Spotify and Tidal
- ⚡ **Rate Limited**: Respects API limits to avoid being blocked

## Prerequisites

### 1. Spotify Developer Account
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Note your `Client ID` and `Client Secret`
4. Add `http://localhost:8888/callback` to Redirect URIs

### 2. Tidal Account
- Active Tidal subscription (required for playlist creation)
- The script uses Tidal's REST API with OAuth2 PKCE flow

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
```bash
# Copy the example file
cp spotify_tidal_env_example.txt .env

# Edit .env with your Spotify credentials
SPOTIFY_CLIENT_ID=your_actual_client_id
SPOTIFY_CLIENT_SECRET=your_actual_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

## Usage

### Basic Usage
```bash
# Transfer using Spotify playlist ID
python spotify_to_tidal_transfer.py 37i9dQZF1DXcBWIGoYBM5M

# Transfer using full Spotify URL
python spotify_to_tidal_transfer.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
```

### Advanced Usage
```bash
# Verbose output
python spotify_to_tidal_transfer.py 37i9dQZF1DXcBWIGoYBM5M --verbose
```

## How It Works

### 1. **Spotify Authentication**
- Uses OAuth2 flow to authenticate with Spotify
- Caches tokens in `.spotify_cache` for reuse

### 2. **Playlist Extraction**
- Fetches playlist metadata (name, description)
- Retrieves all tracks with pagination support
- Extracts track details: name, artists, album, ISRC

### 3. **Tidal Authentication**
- Interactive OAuth2 PKCE login (opens browser automatically)
- Saves tokens in `.tidal_tokens.json` for reuse
- Uses Tidal's public client credentials

### 4. **Track Matching**
- **Primary**: Searches by ISRC code (most accurate)
- **Fallback**: Searches by artist + track name
- **Smart Matching**: Compares artist names for best match

### 5. **Playlist Creation**
- Creates new playlist on Tidal with same name
- Adds description with "Transferred from Spotify" note
- Adds matched tracks one by one

## Example Output

```
🎵 Spotify to Tidal Playlist Transfer
========================================
🎵 Fetching Spotify playlist: 37i9dQZF1DXcBWIGoYBM5M
✅ Found 50 tracks in playlist 'Today's Top Hits'
📝 Creating Tidal playlist: 'Today's Top Hits'
✅ Created Tidal playlist: Today's Top Hits
🎵 Adding 50 tracks to Tidal playlist...
  [1/50] Searching: Taylor Swift - Anti-Hero
    ✅ Added: Taylor Swift - Anti-Hero
  [2/50] Searching: Harry Styles - As It Was
    ✅ Added: Harry Styles - As It Was
  ...

📊 Transfer Summary:
  Total tracks: 50
  ✅ Successfully added: 47
  ⚠️  Not found on Tidal: 2
  ❌ Errors: 1

🔍 Tracks not found on Tidal:
  - Artist Name - Rare Track Name
  - Another Artist - Unreleased Song

🎯 Success rate: 94.0%

🎉 Playlist transfer completed!
```

## Troubleshooting

### Common Issues

1. **"Missing Spotify credentials"**
   - Make sure `.env` file exists with correct credentials
   - Verify credentials are valid in Spotify Developer Dashboard

2. **"Failed to login to Tidal"**
   - Ensure you have an active Tidal subscription
   - Try deleting `.tidal_tokens.json` and logging in again
   - Make sure you copy the full authorization code from the redirect URL

3. **"Rate limit exceeded"**
   - The script includes rate limiting, but if you hit limits:
   - Wait a few minutes and try again
   - Reduce the playlist size for testing

4. **Low success rate**
   - Some tracks may not be available on Tidal
   - Regional availability differences
   - Different track versions (explicit vs clean)

### Debug Mode
```bash
# Run with verbose output for debugging
python spotify_to_tidal_transfer.py PLAYLIST_ID --verbose
```

## API Limits

- **Spotify**: 100 requests per minute per user
- **Tidal**: Unofficial limits, script includes 0.5s delays
- **Recommendation**: Don't transfer huge playlists (>500 tracks) frequently

## File Structure

```
├── spotify_to_tidal_transfer.py  # Main script
├── requirements.txt              # Python dependencies
├── spotify_tidal_env_example.txt # Environment variables template
├── .spotify_cache               # Spotify token cache (auto-generated)
├── .tidal_tokens.json          # Tidal token cache (auto-generated)
└── .env                        # Your credentials (create this)
```

## Security Notes

- Never commit `.env` file to version control
- Token caches (`.spotify_cache`, `.tidal_tokens.json`) contain sensitive data
- Credentials are only used for API authentication, not stored remotely

## Limitations

- Can only transfer public and your own playlists from Spotify
- Some tracks may not be available on Tidal due to licensing
- Tidal requires active subscription for playlist creation
- Transfer is one-way (Spotify → Tidal only)

## Contributing

Feel free to improve the script:
- Better track matching algorithms
- Support for other streaming services
- Batch playlist transfers
- GUI interface
