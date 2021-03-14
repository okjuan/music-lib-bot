from collections import defaultdict
from datetime import datetime, timedelta
from random import shuffle
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth


SPOTIFY_CLIENT = None
SPOTIFY_SCOPES = "user-library-read,playlist-modify-private"
ISO8601_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
NUM_DAYS_TO_LOOK_BACK = 15
NUM_TRACKS_PER_ALBUM = 3

def get_spotify_creds():
    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    secret_key = os.environ.get("SPOTIPY_CLIENT_SECRET")
    if client_id is None or secret_key is None:
        raise Exception("Env vars 'SPOTIPY_CLIENT_ID' and 'SPOTIPY_CLIENT_SECRET' must be set.")
    return client_id, secret_key

def get_spotify_bearer_token():
    return os.environ.get("SPOTIFY_BEARER_TOKEN")

def add_albums_to_playlist(all_albums):
    if len(all_albums) == 0:
        return

    albums_by_genre = group_albums_by_genre(all_albums)
    for description, albums in albums_by_genre.items():
        create_playlist(
            "created by music.lib.bot",
            get_tracks_from_each(albums),
            description=description
        )

def get_tracks_from_each(albums):
    tracks = [
        track
        for album in albums
        for track in get_most_popular_tracks(album, NUM_TRACKS_PER_ALBUM)
    ]
    shuffle(tracks)
    return tracks

def group_albums_by_genre(albums):
    """
    Returns:
        albums_by_genre (dict): key:string, value:[Album].
            e.g. {'rock': [Album], 'jazz': [Album, Album]}.
    """
    for album in albums:
        album['genres'] = get_genres(album)

    album_groups = _group_albums_by_genre(albums)
    album_groups_by_genre_string = dict()
    for album_group in album_groups:
        # TODO: move this logic to _group_albums_by_genre, where we should already know it?
        genres = set(album_group[0]['genres'])
        for album in album_group[1:]:
            genres &= set(album['genres'])
        album_groups_by_genre_string[get_genre_key_string(genres)] = album_group
    return album_groups_by_genre_string

def _group_albums_by_genre(albums):
    """Determine which albums have similar genres."""
    adjacencies, genre_to_albums = defaultdict(lambda: defaultdict(int)), defaultdict(set)
    albums_by_id = dict()
    for album in albums:
        for genre in album['genres']:
            for matching_album_id in genre_to_albums[genre]:
                adjacencies[album['id']][matching_album_id] += 1
                adjacencies[matching_album_id][album['id']] += 1
            genre_to_albums[genre].add(album['id'])
        albums_by_id[album['id']] = album

    album_ids = albums_by_id.keys()
    min_genres_in_common, albums_to_group = 1, set(album_ids)
    grouped_albums = []
    for album_id in album_ids:
        if album_id not in albums_to_group:
            continue

        group = []
        for matching_album_id, num_matches in adjacencies[album_id].items():
            if num_matches >= min_genres_in_common:
                group.append(albums_by_id[matching_album_id])
                albums_to_group.remove(matching_album_id)
        group.append(albums_by_id[album_id])
        albums_to_group.remove(album_id)
        grouped_albums.append(group)

    return grouped_albums

def get_genres(album):
    return [
        genre
        for artist in album['artists']
        for genre in spotify_client().artist(artist['id'])['genres']
    ]

def get_genre_key_string(genres):
    return ", ".join(genres) if len(genres) > 0 else "unknown genre"

def create_playlist(name, tracks, description=""):
    user_id = spotify_client().me()['id']
    playlist = spotify_client().user_playlist_create(
        user_id, name, public=False, description=description)

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