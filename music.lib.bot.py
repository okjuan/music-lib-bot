import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth


def get_spotify_creds():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    secret_key = os.environ.get("SPOTIFY_SECRET_KEY")
    if client_id is None or secret_key is None:
        raise Exception("Env vars 'SPOTIFY_CLIENT_ID' and 'SPOTIFY_SECRET_KEY' must be set.")
    return client_id, secret_key

def get_spotify_bearer_token():
    return os.environ.get("SPOTIFY_BEARER_TOKEN")

scope = "user-library-read"
client_id, client_secret = get_spotify_creds()

auth = SpotifyOAuth(scope=scope)
spotify = spotipy.Spotify(auth_manager=auth)
results = spotify.current_user_saved_tracks()
for idx, item in enumerate(results['items']):
    track = item['track']
    print(idx, track['artists'][0]['name'], " – ", track['name'])