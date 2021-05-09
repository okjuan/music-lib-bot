from spotipy.oauth2 import SpotifyOAuth
import spotipy

from models.album import Album
from models.playlist import Playlist
from models.track import Track

SPOTIFY_ALBUMS_API_LIMIT = 50
SPOTIFY_ADD_TRACKS_TO_PLAYLIST_API_LIMIT = 100
SPOTIFY_SCOPES = "user-library-read,playlist-modify-private,playlist-modify-private,playlist-read-private,playlist-read-collaborative"


class SpotifyClientWrapper:
    def __init__(self):
        auth = SpotifyOAuth(scope=SPOTIFY_SCOPES)
        self.client = spotipy.Spotify(auth_manager=auth)

    def get_current_user_playlist(self, name):
        playlist_id = self.search_current_user_playlists(name)
        if playlist_id is None:
            return None

        return self.get_playlist(playlist_id)

    def get_playlist(self, playlist_id):
        return Playlist.from_spotify_playlist(self.client.playlist(playlist_id))

    def search_current_user_playlists(self, playlist_name):
        "Returns playlist ID or None if not found."
        num_playlists_fetched = 0
        while True:
            playlists = self.client.current_user_playlists(
                offset=num_playlists_fetched).get('items', [])
            if len(playlists) == 0:
                break
            num_playlists_fetched += len(playlists)
            for playlist in playlists:
                if playlist['name'] == playlist_name:
                    return playlist['id']
        return None

    def get_artist_genres(self, artist_id):
        return self.client.artist(artist_id)['genres']

    def get_my_albums(self, max_albums_to_fetch):
        print(f"Fetching recently saved albums...")
        albums, albums_fetched_so_far = [], 0
        while albums_fetched_so_far < max_albums_to_fetch:
            max_batch_size = max_albums_to_fetch - albums_fetched_so_far

            batch_size = max_batch_size if max_batch_size <= SPOTIFY_ALBUMS_API_LIMIT else SPOTIFY_ALBUMS_API_LIMIT
            results = self.client.current_user_saved_albums(
                limit=batch_size, offset=albums_fetched_so_far)

            if len(results['items']) == 0:
                print(f"No albums left to fetch...")
                break

            albums.extend([album['album'] for album in results['items']])
            albums_fetched_so_far += batch_size

        print(f"Fetched {len(albums)} albums...")
        return albums

    def get_track(self, track_id):
        return Track.from_spotify_track(self.client.track(track_id))

    def get_album(self, album_id):
        return Album.from_spotify_album(self.client.album(album_id))

    def create_playlist(self, name, description):
        user_id = self.client.me()['id']
        playlist = self.client.user_playlist_create(
            user_id, name, public=False, description=description)
        return Playlist.from_spotify_playlist(playlist)

    def add_tracks(self, playlist_id, track_uris):
        items, num_tracks_added_so_far, num_tracks_to_add = [], 0, len(track_uris)
        while num_tracks_added_so_far < num_tracks_to_add:
            num_items_left_to_fetch = num_tracks_to_add - num_tracks_added_so_far
            batch_size = num_items_left_to_fetch if num_items_left_to_fetch <= SPOTIFY_ADD_TRACKS_TO_PLAYLIST_API_LIMIT else SPOTIFY_ADD_TRACKS_TO_PLAYLIST_API_LIMIT
            self.client.user_playlist_add_tracks(
                self.client.me()['id'],
                playlist_id,
                track_uris[num_tracks_added_so_far:num_tracks_added_so_far+batch_size],
            )
            num_tracks_added_so_far += batch_size