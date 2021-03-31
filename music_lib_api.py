from collections import defaultdict
from random import shuffle
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth


SPOTIFY_SCOPES = "user-library-read,playlist-modify-private"

# To prevent fetching a copious amount of albums and overwhelming memory
MAX_ALBUMS_TO_FETCH = 1000

class MusicLibApi:
    def __init__(self):
        self.spotify_client = self.spotify_client()

    def create_playlist(self, name, tracks, description=""):
        user_id = self.spotify_client.me()['id']
        playlist = self.spotify_client.user_playlist_create(
            user_id, name, public=False, description=description)

        track_uris = [track['uri'] for track in tracks]
        self.spotify_client.user_playlist_add_tracks(user_id, playlist['id'], track_uris)

    def get_tracks_from_each(self, albums, num_tracks_per_album):
        tracks = [
            track
            for album in albums
            for track in self.get_most_popular_tracks(album, num_tracks_per_album)
        ]
        shuffle(tracks)
        return tracks

    def spotify_client(self):
        auth = SpotifyOAuth(scope=SPOTIFY_SCOPES)
        return spotipy.Spotify(auth_manager=auth)