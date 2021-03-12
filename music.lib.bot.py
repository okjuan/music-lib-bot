from datetime import datetime, timedelta
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth


SPOTIFY_SCOPES = "user-library-read"
ISO8601_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
NUM_DAYS_TO_LOOK_BACK = 1

def get_spotify_creds():
    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    secret_key = os.environ.get("SPOTIPY_CLIENT_SECRET")
    if client_id is None or secret_key is None:
        raise Exception("Env vars 'SPOTIPY_CLIENT_ID' and 'SPOTIPY_CLIENT_SECRET' must be set.")
    return client_id, secret_key

def get_spotify_bearer_token():
    return os.environ.get("SPOTIFY_BEARER_TOKEN")

def add_album_to_playlist(album):
    print(f"Ok, this is where I do stuff with {album['name']} by {album['artists'][0]['name']}")

def get_spotify_client():
    client_id, client_secret = get_spotify_creds()
    auth = SpotifyOAuth(scope=SPOTIFY_SCOPES)
    return spotipy.Spotify(auth_manager=auth)

def get_time_utc(time_utc_str):
    return datetime.strptime(time_utc_str, ISO8601_TIMESTAMP_FORMAT)

def was_added_recently(time_added):
    now = datetime.utcnow()
    look_back = timedelta(NUM_DAYS_TO_LOOK_BACK)
    return now - look_back < time_added

def main():
    spotify = get_spotify_client()

    # dict w/ keys: ['href', 'items', 'limit', 'next', 'offset', 'previous', 'total']
    results = spotify.current_user_saved_albums()

    # list, each item is a dict w/ keys: ['added_at', 'album']
    for album in results['items']:
        time_added = get_time_utc(album['added_at'])
        if was_added_recently(time_added):
            add_album_to_playlist(album['album'])


if __name__ == "__main__":
    main()