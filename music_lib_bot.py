from datetime import datetime, timedelta
from random import shuffle
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth


SPOTIFY_CLIENT = None
SPOTIFY_SCOPES = "user-library-read,playlist-modify-private"
ISO8601_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
NUM_DAYS_TO_LOOK_BACK = 1
NUM_TRACKS_PER_ALBUM = 3

def get_spotify_creds():
    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    secret_key = os.environ.get("SPOTIPY_CLIENT_SECRET")
    if client_id is None or secret_key is None:
        raise Exception("Env vars 'SPOTIPY_CLIENT_ID' and 'SPOTIPY_CLIENT_SECRET' must be set.")
    return client_id, secret_key

def get_spotify_bearer_token():
    return os.environ.get("SPOTIFY_BEARER_TOKEN")

def add_albums_to_playlist(albums):
    if len(albums) == 0:
        return

    tracks = [
        track
        for album in albums
        for track in get_most_popular_tracks(album, NUM_TRACKS_PER_ALBUM)
    ]
    shuffle(tracks)

    create_playlist("created by music.lib.bot", tracks)

def create_playlist(name, tracks):
    user_id = spotify_client().me()['id']
    playlist = spotify_client().user_playlist_create(user_id, name, public=False)

    track_uris = [track['uri'] for track in tracks]
    spotify_client().user_playlist_add_tracks(user_id, playlist['id'], track_uris)

def get_most_popular_tracks(album, num_tracks):
    all_tracks = get_tracks_most_popular_first(album)
    return all_tracks[:min(NUM_TRACKS_PER_ALBUM, len(all_tracks))]

def get_tracks_most_popular_first(album):
    tracks_w_metadata = [
        spotify_client().track(track['uri'])
        for track in album['tracks']['items']
    ]
    return sorted(
        tracks_w_metadata,
        key=lambda track: track['popularity'],
        reverse=True
    )

def spotify_client():
    global SPOTIFY_CLIENT
    if SPOTIFY_CLIENT is None:
        client_id, client_secret = get_spotify_creds()
        auth = SpotifyOAuth(scope=SPOTIFY_SCOPES)
        SPOTIFY_CLIENT = spotipy.Spotify(auth_manager=auth)
    return SPOTIFY_CLIENT

def get_time_utc(time_utc_str):
    return datetime.strptime(time_utc_str, ISO8601_TIMESTAMP_FORMAT)

def was_added_recently(time_added):
    now = datetime.utcnow()
    look_back = timedelta(NUM_DAYS_TO_LOOK_BACK)
    return now - look_back < time_added

def make_playlists_from_recently_added_albums():
    results = spotify_client().current_user_saved_albums()
    add_albums_to_playlist([
        album['album']
        for album in results['items']
        if was_added_recently(get_time_utc(album['added_at']))
    ])

if __name__ == "__main__":
    make_playlists_from_recently_added_albums()