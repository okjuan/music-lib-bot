from collections import defaultdict
from datetime import datetime, timedelta
from random import shuffle
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth


SPOTIFY_ALBUMS_API_LIMIT = 50
SPOTIFY_CLIENT = None
SPOTIFY_SCOPES = "user-library-read,playlist-modify-private"
ISO8601_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
ALBUMS_TO_FETCH = 10
LOOK_AT_ENTIRE_LIBRARY = True
MIN_ALBUMS_PER_PLAYLIST = 8
NUM_DAYS_TO_LOOK_BACK = 15
MIN_MATCHES_TO_GROUP = 4
NUM_TRACKS_PER_ALBUM = 3

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
    albums_by_id = add_artist_genres(albums)
    matches = detect_genre_matches(albums_by_id)
    album_groups = group_albums(albums_by_id.keys(), matches)
    return {
        description: [albums_by_id[album_id] for album_id in group["album ids"]]
        for description, group in album_groups.items()
        if group["num matches"] >= MIN_MATCHES_TO_GROUP
    }

def add_artist_genres(albums):
    albums_by_id = dict()
    for album in albums:
        album['genres'] = get_artist_genres(album)
        albums_by_id[album['id']] = album
    return albums_by_id

def group_albums(album_ids, matches):
    if len(album_ids) == 0 or len(matches) == 0:
        return [album_ids]

    grouped_albums = dict()
    for album_id in album_ids:
        for matching_album_id, matched_on in matches[album_id].items():
            group_key = as_readable_key(matched_on)
            if group_key not in grouped_albums:
                grouped_albums[group_key] = {"num matches": 0, "album ids": set()}
            grouped_albums[group_key]["num matches"] = len(matched_on)
            grouped_albums[group_key]["album ids"].add(album_id)
            grouped_albums[group_key]["album ids"].add(matching_album_id)
    return grouped_albums

def detect_genre_matches(albums_by_id):
    adjacencies, genre_to_albums = defaultdict(lambda: defaultdict(list)), defaultdict(set)
    for _, album in albums_by_id.items():
        for genre in album['genres']:
            for matching_album_id in genre_to_albums[genre]:
                adjacencies[album['id']][matching_album_id].append(genre)
                adjacencies[matching_album_id][album['id']].append(genre)
            genre_to_albums[genre].add(album['id'])
    return adjacencies

def get_artist_genres(album):
    return [
        genre
        for artist in album['artists']
        for genre in spotify_client().artist(artist['id'])['genres']
    ]

def as_readable_key(list_):
    list_.sort()
    return ", ".join(list_) if len(list_) > 0 else "unknown"

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
        auth = SpotifyOAuth(scope=SPOTIFY_SCOPES)
        SPOTIFY_CLIENT = spotipy.Spotify(auth_manager=auth)
    return SPOTIFY_CLIENT

def get_time_utc(time_utc_str):
    return datetime.strptime(time_utc_str, ISO8601_TIMESTAMP_FORMAT)

def was_added_recently(time_added):
    now = datetime.utcnow()
    look_back = timedelta(NUM_DAYS_TO_LOOK_BACK)
    return now - look_back < time_added

def fetch_albums():
    all_results, albums_fetched_so_far = [], 0
    while albums_fetched_so_far < ALBUMS_TO_FETCH:
        albums_to_fetch = ALBUMS_TO_FETCH - albums_fetched_so_far
        batch_size = albums_to_fetch if albums_to_fetch <= SPOTIFY_ALBUMS_API_LIMIT else SPOTIFY_ALBUMS_API_LIMIT
        all_results.append(spotify_client().current_user_saved_albums(
            limit=batch_size, offset=albums_fetched_so_far))
        albums_fetched_so_far += batch_size
    return [
        (album['added_at'], album['album'])
        for results in all_results
        for album in results['items']
    ]

def get_my_albums_grouped_by_genre():
    print(f"Fetching recently saved albums...")
    albums = fetch_albums()

    print(f"Fetched {len(albums)} albums...")
    if len(albums) == 0:
        return {}

    print(f"Grouping {len(albums)} albums...")
    albums_by_genre = group_albums_by_genre([
        album
        for timestamp, album in albums
        if LOOK_AT_ENTIRE_LIBRARY or was_added_recently(get_time_utc(timestamp))
    ])

    print(f"Matched into {len(albums_by_genre)} groups...")
    return albums_by_genre