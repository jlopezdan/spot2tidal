#!/usr/bin/env python3
"""
Spotify to Tidal Playlist Transfer Script

This script fetches playlist information from Spotify and creates 
a corresponding playlist in Tidal with the same tracks.

Requirements:
- spotipy (Spotify Web API wrapper)
- requests (HTTP library)
- python-dotenv (for environment variables)

Install with: pip install spotipy requests python-dotenv
"""

import os
import sys
import time
import json
import base64
import hashlib
import secrets
import urllib.parse
import webbrowser
from typing import List, Dict, Optional
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import argparse

# Load environment variables
load_dotenv()

class TidalAPI:
    """Tidal REST API client"""
    
    def __init__(self):
        self.base_url = "https://api.tidal.com/v1"
        self.auth_url = "https://auth.tidal.com/v1/oauth2"
        self.client_id = "zU4XHVVkc2tDPo4t"  # Tidal's public client ID
        self.client_secret = "VJKhDFqJPqvsPVNBV6ukXTJmwlvbttP7wlMlrc72se4="
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.country_code = None
        self.session = requests.Session()
        
    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    def _generate_code_challenge(self, verifier: str) -> str:
        """Generate PKCE code challenge"""
        digest = hashlib.sha256(verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    
    def login(self) -> bool:
        """Login to Tidal using OAuth2 PKCE flow"""
        try:
            # Check if we have saved tokens
            if self._load_tokens():
                if self._refresh_access_token():
                    print("✅ Loaded existing Tidal session")
                    return True
            
            print("🔐 Logging into Tidal...")
            
            # Generate PKCE parameters
            code_verifier = self._generate_code_verifier()
            code_challenge = self._generate_code_challenge(code_verifier)
            
            # Authorization URL
            auth_params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': 'http://localhost:8080',
                'scope': 'r_usr w_usr',
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256'
            }
            
            auth_url = f"{self.auth_url}/authorize?" + urllib.parse.urlencode(auth_params)
            print(f"Please visit this URL to authorize: {auth_url}")
            
            # Open browser automatically
            webbrowser.open(auth_url)
            
            # Get authorization code from user
            auth_code = input("Enter the authorization code from the redirect URL: ").strip()
            
            # Exchange code for tokens
            token_data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': auth_code,
                'redirect_uri': 'http://localhost:8080',
                'code_verifier': code_verifier
            }
            
            response = requests.post(f"{self.auth_url}/token", data=token_data)
            
            if response.status_code == 200:
                token_info = response.json()
                self.access_token = token_info['access_token']
                self.refresh_token = token_info.get('refresh_token')
                
                # Get user info
                if self._get_user_info():
                    self._save_tokens()
                    print("✅ Successfully logged into Tidal")
                    return True
            
            print(f"❌ Failed to get access token: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def _load_tokens(self) -> bool:
        """Load saved tokens from file"""
        try:
            if os.path.exists('.tidal_tokens.json'):
                with open('.tidal_tokens.json', 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
                    self.user_id = data.get('user_id')
                    self.country_code = data.get('country_code')
                    return bool(self.access_token)
        except Exception:
            pass
        return False
    
    def _save_tokens(self):
        """Save tokens to file"""
        try:
            data = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'user_id': self.user_id,
                'country_code': self.country_code
            }
            with open('.tidal_tokens.json', 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"⚠️  Failed to save tokens: {e}")
    
    def _refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            return False
        
        try:
            token_data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token
            }
            
            response = requests.post(f"{self.auth_url}/token", data=token_data)
            
            if response.status_code == 200:
                token_info = response.json()
                self.access_token = token_info['access_token']
                if 'refresh_token' in token_info:
                    self.refresh_token = token_info['refresh_token']
                self._save_tokens()
                return True
                
        except Exception as e:
            print(f"⚠️  Failed to refresh token: {e}")
        
        return False
    
    def _get_user_info(self) -> bool:
        """Get user information"""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = self.session.get(f"{self.base_url}/users/me", headers=headers)
            
            if response.status_code == 200:
                user_info = response.json()
                self.user_id = user_info['id']
                self.country_code = user_info['countryCode']
                return True
        except Exception as e:
            print(f"⚠️  Failed to get user info: {e}")
        
        return False
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make authenticated request to Tidal API"""
        if not self.access_token:
            return None
        
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle token expiration
            if response.status_code == 401:
                if self._refresh_access_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = self.session.request(method, url, **kwargs)
            
            return response
        except Exception as e:
            print(f"⚠️  API request error: {e}")
            return None
    
    def search_tracks(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for tracks"""
        params = {
            'query': query,
            'type': 'TRACKS',
            'limit': limit,
            'countryCode': self.country_code
        }
        
        response = self._make_request('GET', '/search', params=params)
        
        if response and response.status_code == 200:
            data = response.json()
            return data.get('tracks', {}).get('items', [])
        
        return []
    
    def create_playlist(self, title: str, description: str = "") -> Optional[Dict]:
        """Create a new playlist"""
        data = {
            'title': title,
            'description': description
        }
        
        response = self._make_request('POST', f'/users/{self.user_id}/playlists', json=data)
        
        if response and response.status_code == 201:
            return response.json()
        
        return None
    
    def add_tracks_to_playlist(self, playlist_uuid: str, track_ids: List[int]) -> bool:
        """Add tracks to playlist"""
        data = {
            'trackIds': ','.join(map(str, track_ids))
        }
        
        response = self._make_request('POST', f'/playlists/{playlist_uuid}/tracks', data=data)
        
        return response and response.status_code == 200

class SpotifyToTidalTransfer:        
    def _init_spotify(self) -> spotipy.Spotify:
        """Initialize Spotify client with OAuth"""
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
        
        return spotipy.Spotify(auth_manager=auth_manager)
    
    def __init__(self):
        """Initialize Spotify and Tidal clients"""
        self.spotify = self._init_spotify()
        self.tidal = TidalAPI()
        self._init_tidal()
    
    def _init_tidal(self) -> bool:
        """Initialize Tidal API client"""
        if not self.tidal.login():
            raise Exception("Failed to login to Tidal")
        return True
    
    def get_spotify_playlist(self, playlist_id: str) -> Dict:
        """Fetch playlist information from Spotify"""
        try:
            print(f"🎵 Fetching Spotify playlist: {playlist_id}")
            
            # Get playlist metadata
            playlist = self.spotify.playlist(playlist_id)
            
            # Get all tracks (handle pagination)
            tracks = []
            results = self.spotify.playlist_tracks(playlist_id)
            
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
            return playlist_info
            
        except Exception as e:
            print(f"❌ Error fetching Spotify playlist: {e}")
            raise
    
    def search_tidal_track(self, track_info: Dict) -> Optional[Dict]:
        """Search for a track on Tidal"""
        try:
            # Try searching by ISRC first (most accurate)
            if track_info.get('isrc'):
                search_results = self.tidal.search_tracks(track_info['isrc'], limit=5)
                if search_results:
                    return search_results[0]
            
            # Fallback to artist + track name search
            artist_names = ' '.join(track_info['artists'])
            query = f"{artist_names} {track_info['name']}"
            
            search_results = self.tidal.search_tracks(query, limit=10)
            
            if search_results:
                # Try to find the best match
                for track in search_results:
                    # Check if artist names match (case-insensitive)
                    tidal_artists = [artist['name'].lower() for artist in track.get('artists', [])]
                    spotify_artists = [artist.lower() for artist in track_info['artists']]
                    
                    # Check for artist overlap
                    if any(spotify_artist in ' '.join(tidal_artists) for spotify_artist in spotify_artists):
                        return track
                
                # If no perfect match, return the first result
                return search_results[0]
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error searching for track '{track_info['name']}': {e}")
            return None
    
    def create_tidal_playlist(self, playlist_info: Dict) -> Optional[Dict]:
        """Create a new playlist on Tidal"""
        try:
            print(f"📝 Creating Tidal playlist: '{playlist_info['name']}'")
            
            # Create the playlist
            description = f"{playlist_info['description']}\n\n🎵 Transferred from Spotify"
            playlist = self.tidal.create_playlist(
                title=playlist_info['name'],
                description=description
            )
            
            if playlist:
                print(f"✅ Created Tidal playlist: {playlist['title']}")
                return playlist
            else:
                raise Exception("Failed to create playlist")
                
        except Exception as e:
            print(f"❌ Error creating Tidal playlist: {e}")
            return None
    
    def add_tracks_to_tidal_playlist(self, playlist: Dict, tracks: List[Dict]) -> Dict:
        """Add tracks to the Tidal playlist"""
        results = {
            'added': 0,
            'not_found': 0,
            'errors': 0,
            'not_found_tracks': []
        }
        
        print(f"🎵 Adding {len(tracks)} tracks to Tidal playlist...")
        
        # Collect track IDs to add in batches
        track_ids_to_add = []
        
        for i, track_info in enumerate(tracks, 1):
            try:
                print(f"  [{i}/{len(tracks)}] Searching: {track_info['artists'][0]} - {track_info['name']}")
                
                # Search for track on Tidal
                tidal_track = self.search_tidal_track(track_info)
                
                if tidal_track:
                    track_ids_to_add.append(tidal_track['id'])
                    artist_name = tidal_track.get('artists', [{}])[0].get('name', 'Unknown')
                    print(f"    ✅ Found: {artist_name} - {tidal_track['title']}")
                else:
                    results['not_found'] += 1
                    results['not_found_tracks'].append(f"{track_info['artists'][0]} - {track_info['name']}")
                    print(f"    ⚠️  Not found: {track_info['artists'][0]} - {track_info['name']}")
                
                # Add tracks in batches of 100 to avoid API limits
                if len(track_ids_to_add) >= 100:
                    success = self.tidal.add_tracks_to_playlist(playlist['uuid'], track_ids_to_add)
                    if success:
                        results['added'] += len(track_ids_to_add)
                        print(f"    ✅ Added batch of {len(track_ids_to_add)} tracks")
                    else:
                        results['errors'] += len(track_ids_to_add)
                        print(f"    ❌ Failed to add batch of {len(track_ids_to_add)} tracks")
                    track_ids_to_add = []
                
                # Rate limiting - be nice to the APIs
                time.sleep(0.3)
                
            except Exception as e:
                results['errors'] += 1
                print(f"    ❌ Error processing track: {e}")
        
        # Add remaining tracks
        if track_ids_to_add:
            success = self.tidal.add_tracks_to_playlist(playlist['uuid'], track_ids_to_add)
            if success:
                results['added'] += len(track_ids_to_add)
                print(f"    ✅ Added final batch of {len(track_ids_to_add)} tracks")
            else:
                results['errors'] += len(track_ids_to_add)
                print(f"    ❌ Failed to add final batch of {len(track_ids_to_add)} tracks")
        
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
