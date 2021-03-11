from datetime import datetime, timedelta
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth


ISO8601_TIMESTAMP = "%Y-%m-%dT%H:%M:%SZ"
NUM_DAYS_TO_LOOK_BACK = 1

def get_spotify_creds():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    secret_key = os.environ.get("SPOTIFY_SECRET_KEY")
    if client_id is None or secret_key is None:
        raise Exception("Env vars 'SPOTIFY_CLIENT_ID' and 'SPOTIFY_SECRET_KEY' must be set.")
    return client_id, secret_key

def get_spotify_bearer_token():
    return os.environ.get("SPOTIFY_BEARER_TOKEN")

def add_album_to_playlist(album):
    print(f"Ok, this is where I do stuff with {album['name']} by {album['artists'][0]['name']}")

scope = "user-library-read"
client_id, client_secret = get_spotify_creds()

auth = SpotifyOAuth(scope=scope)
spotify = spotipy.Spotify(auth_manager=auth)

# dict w/ keys: ['href', 'items', 'limit', 'next', 'offset', 'previous', 'total']
results = spotify.current_user_saved_albums()

# list, each item is a dict w/ keys: ['added_at', 'album']
for album in results['items']:
    time_added = datetime.strptime(album['added_at'], ISO8601_TIMESTAMP)
    now = datetime.utcnow()
    look_back = timedelta(NUM_DAYS_TO_LOOK_BACK)
    if now - look_back < time_added:
        add_album_to_playlist(album['album'])