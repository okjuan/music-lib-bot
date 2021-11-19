from spotipy.oauth2 import SpotifyOAuth
import spotipy

from app.models.album import Album
from app.models.audio_features import AudioFeatures
from app.models.artist import Artist
from app.models.playlist import Playlist
from app.models.track import Track

SPOTIFY_ALBUMS_API_LIMIT = 50
SPOTIFY_ADD_TRACKS_TO_PLAYLIST_API_LIMIT = 100
SPOTIFY_SCOPES = "user-library-read,playlist-modify-private,playlist-modify-private,playlist-read-private,playlist-read-collaborative"
RECOMMENDATION_SEED_LIMIT = 5
RECOMMENDATIONS_LIMIT = 100


class SpotifyClientWrapper:
    def __init__(self):
        auth = SpotifyOAuth(scope=SPOTIFY_SCOPES)
        self.client = spotipy.Spotify(auth_manager=auth)

    def get_matching_artists(self, artist_name):
        results = self.client.search(q=f"artist:{artist_name}", type="artist")
        return [
            Artist.from_spotify_artist(item)
            for item in results["artists"]["items"]
        ]

    def get_current_user_playlist_by_name(self, name):
        playlist_id = self.find_current_user_playlist(name)
        if playlist_id is None:
            return None

        playlist = self.get_playlist(playlist_id)
        return playlist

    def get_playlist(self, playlist_id):
        playlist = Playlist.from_spotify_playlist(
            self.client.playlist(playlist_id))
        playlist.tracks = self._get_playlist_tracks(playlist.id)
        return playlist

    def _get_playlist_tracks(self, playlist_id):
        def track_fetcher(offset=0):
            results = self.client.playlist_tracks(
                playlist_id, offset=offset)
            return results['items'], results['total']

        playlist_track_metadata = self._fetch_until_all_items_returned(track_fetcher)
        return [
            Track.from_spotify_playlist_track(track)
            for track in playlist_track_metadata
        ]

    def find_current_user_playlist(self, playlist_name):
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

    def get_artist_albums(self, artist_id):
        def album_fetcher(offset=0):
            results = self.client.artist_albums(
                artist_id, album_type="album", offset=offset)
            return results['items'], results['total']
        albums_metadata = self._fetch_until_all_items_returned(album_fetcher)
        return self.get_albums(
            [album['id'] for album in albums_metadata])

    def _fetch_until_all_items_returned(self, fetch_func):
        """
        Params:
            fetch_func (func): optional param 'offset',
                returns a 2-tuple where:
                - ([dict]) 1st item is the fetched items
                - (int) 2nd item is the total items
        """
        all_items, total = fetch_func()
        num_results_fetched = len(all_items)
        while num_results_fetched < total:
            offset = num_results_fetched
            items, total = fetch_func(offset=offset)
            num_results_fetched += len(items)
            all_items.extend(items)
        return all_items

    def get_my_albums(self, max_albums_to_fetch):
        def my_album_fetcher(offset=0):
            results = self.client.current_user_saved_albums(offset=offset)
            num_results = len(results['items'])
            items = results['items'][:min(num_results, max_albums_to_fetch)]
            albums = [item['album'] for item in items]
            return albums, max_albums_to_fetch
        albums_metadata = self._fetch_until_all_items_returned(my_album_fetcher)
        return self.get_albums(
            [album['id'] for album in albums_metadata])

    def get_tracks(self, track_ids):
        def track_fetcher(track_ids):
            results = self.client.tracks(track_ids)
            return results['tracks']
        tracks = self._fetch_in_batches(track_ids, track_fetcher)
        return [
            Track.from_spotify_track(track)
            for track in tracks
        ]

    def get_albums(self, album_ids):
        def album_fetcher(album_ids):
            results = self.client.albums(album_ids)
            return results['albums']
        albums = self._fetch_in_batches(album_ids, album_fetcher)
        return [
            Album.from_spotify_album(album)
            for album in albums
        ]

    def _fetch_in_batches(self, item_ids, fetch_items):
        batch_size = min(20, len(item_ids))
        fetched_items = []
        for batch_start_index in range(0, len(item_ids), batch_size):
            batch_end_index = min(batch_start_index+batch_size, len(item_ids))
            fetched_items.extend(
                fetch_items(item_ids[batch_start_index:batch_end_index]))
        return fetched_items

    def create_playlist(self, name, description):
        user_id = self._get_current_user_id()
        playlist = self.client.user_playlist_create(
            user_id, name, public=False, description=description)
        return Playlist.from_spotify_playlist(playlist)

    def add_tracks(self, playlist_id, track_uris):
        num_tracks_added_so_far, num_tracks_to_add = 0, len(track_uris)
        while num_tracks_added_so_far < num_tracks_to_add:
            num_items_left_to_fetch = num_tracks_to_add - num_tracks_added_so_far
            batch_size = num_items_left_to_fetch if num_items_left_to_fetch <= SPOTIFY_ADD_TRACKS_TO_PLAYLIST_API_LIMIT else SPOTIFY_ADD_TRACKS_TO_PLAYLIST_API_LIMIT
            self.client.user_playlist_add_tracks(
                self._get_current_user_id(),
                playlist_id,
                track_uris[num_tracks_added_so_far:num_tracks_added_so_far+batch_size],
            )
            num_tracks_added_so_far += batch_size

    def add_track_at_position(self, playlist_id, track_uri, position):
        self.client.user_playlist_add_tracks(
            self._get_current_user_id(),
            playlist_id,
            [track_uri],
            position=position,
        )

    def _get_current_user_id(self):
        return self.client.me()['id']

    def get_audio_features_by_track_id(self, track_ids):
        return {
            track_audio_features["id"]: AudioFeatures.from_spotify_audio_features(
                track_audio_features)
            for track_audio_features in self.client.audio_features(track_ids)
        }

    def get_recommendations_based_on_tracks(self, track_ids, num_recommendations, min_audio_features,
     max_audio_features):
        """
        Params:
            tracks_ids ([str]): max length is 5.
            num_recommendations (int): max is 100.
            min_audio_features (AudioFeatures).
            max_audio_features (AudioFeatures).
        """
        if len(track_ids) > RECOMMENDATION_SEED_LIMIT:
            track_ids = track_ids[:RECOMMENDATION_SEED_LIMIT]
        if num_recommendations > RECOMMENDATIONS_LIMIT:
            num_recommendations = RECOMMENDATIONS_LIMIT

        results = self.client.recommendations(
            seed_tracks=track_ids,
            limit=num_recommendations,
            min_danceability=min_audio_features.danceability,
            max_danceability=max_audio_features.danceability,
        )
        return [
            Track.from_spotify_track(track)
            for track in results['tracks']
        ]