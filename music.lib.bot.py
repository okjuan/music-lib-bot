from datetime import datetime, timedelta
from random import shuffle
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth


SPOTIFY_SCOPES = "user-library-read,playlist-modify-private"
ISO8601_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
NUM_DAYS_TO_LOOK_BACK = 1
NUM_SONGS_PER_ALBUM = 3

def get_spotify_creds():
    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    secret_key = os.environ.get("SPOTIPY_CLIENT_SECRET")
    if client_id is None or secret_key is None:
        raise Exception("Env vars 'SPOTIPY_CLIENT_ID' and 'SPOTIPY_CLIENT_SECRET' must be set.")
    return client_id, secret_key

def get_spotify_bearer_token():
    return os.environ.get("SPOTIFY_BEARER_TOKEN")

def add_album_to_playlist(albums):
    tracks = []
    for album in albums:
        tracks.extend(get_most_popular_songs(album, NUM_SONGS_PER_ALBUM))
    shuffle(tracks)
    create_playlist(f"created by music.lib.bot", tracks)

def create_playlist(name, tracks):
    user_id = spotify.me()['id']
    playlist = spotify.user_playlist_create(user_id, name, public=False)

    track_uris = [track['uri'] for track in tracks]
    spotify.user_playlist_add_tracks(user_id, playlist['id'], track_uris)

def get_most_popular_songs(album, num_songs):
    all_tracks = get_songs_most_popular_first(album)
    return all_tracks[:min(NUM_SONGS_PER_ALBUM, len(all_tracks))]

def get_songs_most_popular_first(album):
    tracks_w_metadata = [
        spotify.track(track['uri'])
        for track in album['tracks']['items']
    ]
    return sorted(
        tracks_w_metadata,
        key=lambda track: track['popularity'],
        reverse=True
    )

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

def make_playlists_from_recently_added_albums():
    results = spotify.current_user_saved_albums()
    add_album_to_playlist([
        album['album']
        for album in results['items']
        if was_added_recently(get_time_utc(album['added_at']))
    ])

if __name__ == "__main__":
    spotify = get_spotify_client()
    make_playlists_from_recently_added_albums()