#!/usr/bin/env python3
"""
Spotify to Tidal Playlist Transfer Script

This script fetches playlist information from Spotify and creates 
a corresponding playlist in Tidal with the same tracks.

Requirements:
- spotipy (Spotify Web API wrapper)
- tidalapi (Tidal API wrapper)
- python-dotenv (for environment variables)

Install with: pip install spotipy tidalapi python-dotenv
"""
from dotenv import load_dotenv
import os
import sys
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tidalapi
import argparse

# Load environment variables
load_dotenv()

class SpotifyToTidalTransfer:
    def __init__(self):
        """Initialize Spotify and Tidal clients"""
        self.spotify = self._init_spotify()
        self.tidal = self._init_tidal()
        
    def _init_spotify(self) -> spotipy.Spotify:
        """Initialize Spotify client with OAuth"""
        print("initializing spotify .....")
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
        
        if not client_id or not client_secret:
            raise ValueError("Missing Spotify credentials. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
        
        scope = "playlist-read-private playlist-read-collaborative"
        
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache"
        )
        
        print("ok\n")
        return spotipy.Spotify(auth_manager=auth_manager)
    
    def _init_tidal(self) -> tidalapi.Session:
        """Initialize Tidal session"""
        print("initializing Tidal...")
        client_id = os.getenv("TIDAL_CLIENT_ID")
        client_secret = os.getenv("TIDAL_CLIENT_SECRET")
        session = tidalapi.Session()
        
        # Try to load existing session
        if os.path.exists('.tidal_session'):
            try:
                session.load_oauth_session('.tidal_session')
                if session.check_login():
                    print("✅ Loaded existing Tidal session")
                    return session
            except Exception as e:
                print(f"⚠️  Failed to load Tidal session: {e}")
        
        # Login to Tidal
        print("🔐 Logging into Tidal...")
        # login_url, future = session.login_oauth()
        # print(f"Please visit this URL to authorize: {login_url}")
        session.login_oauth_simple(fn_print=print)
        print(session.check_login())

        token_type = session.token_type
        access_token = session.access_token
        refresh_token = session.refresh_token # Not needed if you don't care about refreshing
        expiry_time = session.expiry_time

        print("y ahora???")

        return session
        
        # # Wait for login completion
        # session.login_oauth_simple(function=future)
        
        # if session.check_login():
        #     session.save_oauth_session('.tidal_session')
        #     print("✅ Successfully logged into Tidal")
        #     return session
        # else:
        #     raise Exception("Failed to login to Tidal")
    
    def get_spotify_playlist(self, playlist_id: str) -> Dict:
        """Fetch playlist information from Spotify"""
        try:
            print(f"🎵 Fetching Spotify playlist: {playlist_id}")
            
            # Get playlist metadata
            playlist = self.spotify.playlist(playlist_id)

            print("retorno de la funcion ok")
            
            # Get all tracks (handle pagination)
            tracks = []
            print("pide tracks...")
            results = self.spotify.playlist_tracks(playlist_id)
            print("retorno ok")
            
            while results:
                tracks.extend(results['items'])
                if results['next']:
                    results = self.spotify.next(results)
                else:
                    break
            
            playlist_info = {
                'name': playlist['name'],
                'description': playlist['description'] or '',
                'tracks': [],
                'total_tracks': len(tracks)
            }
            
            # Extract track information
            for item in tracks:
                if item['track'] and item['track']['type'] == 'track':
                    track = item['track']
                    track_info = {
                        'name': track['name'],
                        'artists': [artist['name'] for artist in track['artists']],
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'isrc': track.get('external_ids', {}).get('isrc'),
                        'spotify_id': track['id']
                    }
                    playlist_info['tracks'].append(track_info)
            
            print(f"✅ Found {len(playlist_info['tracks'])} tracks in playlist '{playlist_info['name']}'")

            # Recorremos la lista de tracks dentro de playlist_info
            for track in playlist_info['tracks']:
                name = track['name']
                isrc = track['isrc']
                
                # Imprimimos los valores (usando un valor por defecto si el ISRC es None)
                print(f"Name: {name} | ISRC: {isrc if isrc else 'N/A'}")            

            return playlist_info
            
        except Exception as e:
            print(f"❌ Error fetching Spotify playlist: {e}")
            raise
    
    def search_tidal_track(self, track_info: Dict) -> Optional[tidalapi.Track]:
        """Search for a track on Tidal"""
        try:
            # Try searching by ISRC first (most accurate)
            if track_info.get('isrc'):
                print("en Spotify tiene isrc, voy a buscar en Tidal....")
                #JLD search_results = self.tidal.search('track', track_info['isrc'])
                isrc_a_buscar = track_info['isrc']
                cad = f"filter%5Bisrc%5D={isrc_a_buscar}"
                print("cad:" + cad)
                search_results = self.tidal.search(cad, models=[tidalapi.Track])
                if search_results:
                    print ("YESSSS")
                    print(search_results)
                    if search_results['tracks']:
                        print ("YESSSS 22222")
                        return search_results['tracks'][0]
            
            # # Fallback to artist + track name search
            # artist_names = ' '.join(track_info['artists'])
            # query = f"{artist_names} {track_info['name']}"
            
            # search_results = self.tidal.search('track', query, limit=10)
            
            # if search_results and search_results['tracks']:
            #     # Try to find the best match
            #     for track in search_results['tracks']:
            #         # Check if artist names match (case-insensitive)
            #         tidal_artists = [artist.name.lower() for artist in track.artists]
            #         spotify_artists = [artist.lower() for artist in track_info['artists']]
                    
            #         # Check for artist overlap
            #         if any(spotify_artist in ' '.join(tidal_artists) for spotify_artist in spotify_artists):
            #             return track
                
            #     # If no perfect match, return the first result
            #     return search_results['tracks'][0]
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error searching for track '{track_info['name']}': {e}")
            return None
    
    def create_tidal_playlist(self, playlist_info: Dict) -> Optional[tidalapi.Playlist]:
        """Create a new playlist on Tidal"""
        try:
            print(f"📝 Creating Tidal playlist: '{playlist_info['name']}'")
            
            # Create the playlist
            playlist = self.tidal.user.create_playlist(
                title=playlist_info['name'],
                description=f"{playlist_info['description']}\n\n🎵 Transferred from Spotify"
            )
            
            if playlist:
                print(f"✅ Created Tidal playlist: {playlist.name}")
                return playlist
            else:
                raise Exception("Failed to create playlist")
                
        except Exception as e:
            print(f"❌ Error creating Tidal playlist: {e}")
            return None
    
    def add_tracks_to_tidal_playlist(self, playlist: tidalapi.Playlist, tracks: List[Dict]) -> Dict:
        """Add tracks to the Tidal playlist"""
        results = {
            'added': 0,
            'not_found': 0,
            'errors': 0,
            'not_found_tracks': []
        }
        
        print(f"🎵 Adding {len(tracks)} tracks to Tidal playlist...")
        
        for i, track_info in enumerate(tracks, 1):
            try:
                print(f"  [{i}/{len(tracks)}] Searching: {track_info['artists'][0]} - {track_info['name']}")
                
                # Search for track on Tidal
                tidal_track = self.search_tidal_track(track_info)
                
                if tidal_track:
                    print("ok in TIDAL")
                    # Add track to playlist
                    success = playlist.add([tidal_track.id])
                    if success:
                        results['added'] += 1
                        print(f"    ✅ Added: {tidal_track.artist.name} - {tidal_track.name}")
                    else:
                        results['errors'] += 1
                        print(f"    ❌ Failed to add: {track_info['artists'][0]} - {track_info['name']}")
                else:
                    print("FAIL in TIDAL")
                    results['not_found'] += 1
                    results['not_found_tracks'].append(f"{track_info['artists'][0]} - {track_info['name']}")
                    print(f"    ⚠️  Not found: {track_info['artists'][0]} - {track_info['name']}")
                
                # Rate limiting - be nice to the APIs
                time.sleep(0.5)
                
            except Exception as e:
                results['errors'] += 1
                print(f"    ❌ Error processing track: {e}")
        
        return results
    
    def transfer_playlist(self, spotify_playlist_id: str) -> bool:
        """Main function to transfer a playlist from Spotify to Tidal"""
        try:
            # Step 1: Get Spotify playlist
            playlist_info = self.get_spotify_playlist(spotify_playlist_id)
            
            # Step 2: Create Tidal playlist
            tidal_playlist = self.create_tidal_playlist(playlist_info)
            if not tidal_playlist:
                return False
            
            # Step 3: Add tracks to Tidal playlist
            results = self.add_tracks_to_tidal_playlist(tidal_playlist, playlist_info['tracks'])
            
            # Step 4: Print summary
            print(f"\n📊 Transfer Summary:")
            print(f"  Total tracks: {len(playlist_info['tracks'])}")
            print(f"  ✅ Successfully added: {results['added']}")
            print(f"  ⚠️  Not found on Tidal: {results['not_found']}")
            print(f"  ❌ Errors: {results['errors']}")
            
            if results['not_found_tracks']:
                print(f"\n🔍 Tracks not found on Tidal:")
                for track in results['not_found_tracks']:
                    print(f"  - {track}")
            
            success_rate = (results['added'] / len(playlist_info['tracks'])) * 100
            print(f"\n🎯 Success rate: {success_rate:.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Transfer failed: {e}")
            return False

def extract_playlist_id(spotify_url: str) -> str:
    """Extract playlist ID from Spotify URL"""
    if 'playlist/' in spotify_url:
        return spotify_url.split('playlist/')[1].split('?')[0]
    return spotify_url

def main():
    parser = argparse.ArgumentParser(description='Transfer Spotify playlist to Tidal')
    parser.add_argument('playlist_id', help='Spotify playlist ID or URL')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Extract playlist ID if URL is provided
    playlist_id = extract_playlist_id(args.playlist_id)
    
    print("🎵 Spotify to Tidal Playlist Transfer")
    print("=" * 40)
    
    try:
        # Initialize the transfer client
        transfer_client = SpotifyToTidalTransfer()
        
        # Perform the transfer
        success = transfer_client.transfer_playlist(playlist_id)
        
        if success:
            print("\n🎉 Playlist transfer completed!")
            sys.exit(0)
        else:
            print("\n💥 Playlist transfer failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Transfer cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
