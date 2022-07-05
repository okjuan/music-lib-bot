from spotipy.oauth2 import SpotifyOAuth
import spotipy

from packages.music_api_clients.models.album import Album
from packages.music_api_clients.models.audio_features import AudioFeatures
from packages.music_api_clients.models.artist import Artist
from packages.music_api_clients.models.playlist import Playlist
from packages.music_api_clients.models.track import Track


API_BATCH_SIZE = 20
SPOTIFY_ALBUMS_API_LIMIT = 50
SPOTIFY_ADD_TRACKS_TO_PLAYLIST_API_LIMIT = 100
SPOTIFY_SCOPES = "user-library-read,playlist-modify-private,playlist-modify-private,playlist-read-private,playlist-read-collaborative"
RECOMMENDATION_SEED_LIMIT = 5
RECOMMENDATIONS_LIMIT = 100


class Spotify:
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

        playlist = self._get_playlist_by_id(playlist_id)
        return playlist

    def get_playlist(self, playlist):
        return self._get_playlist_by_id(playlist.spotify_id)

    def _get_playlist_by_id(self, playlist_id):
        playlist_with_all_data = Playlist.from_spotify_playlist(
            self.client.playlist(playlist_id))
        playlist_with_all_data.tracks = self._get_playlist_tracks(playlist_id)
        return playlist_with_all_data

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

    def find_current_user_matching_playlists(self, keyword):
        def get_playlist_tracks(spotify_playlist_id):
            return lambda: self._get_playlist_tracks(spotify_playlist_id)
        def playlist_fetcher(offset=0):
            results = self.client.current_user_playlists(offset=offset)
            matching_playlists = [
                Playlist.from_spotify_playlist_search_results(
                    playlist, get_playlist_tracks(playlist['id']))
                for playlist in results['items']
                if keyword in playlist['name']
            ]
            finished = len(results['items']) + offset >= results['total']
            return matching_playlists, finished
        playlists = self._fetch_until_all_items_returned(playlist_fetcher)
        return playlists

    def get_artist_genres(self, artist):
        return self.client.artist(artist.spotify_id)['genres']

    def get_artist_albums(self, artist):
        def album_fetcher(offset=0):
            results = self.client.artist_albums(
                artist.spotify_id, album_type="album", offset=offset)
            albums = [
                Album.from_spotify_artist_album(item)
                for item in results['items']
            ]
            finished = len(results['items']) + offset >= results['total']
            return albums, finished
        albums = self._fetch_until_all_items_returned(album_fetcher)
        return self.get_albums(albums)

    def get_my_albums(self, max_albums_to_fetch):
        def my_album_fetcher(offset=0):
            results = self.client.current_user_saved_albums(offset=offset)
            num_results = len(results['items'])
            items = results['items'][:min(num_results, max_albums_to_fetch)]
            albums = [
                Album.from_spotify_album(item['album'])
                for item in items
            ]
            finished = num_results + offset >= max_albums_to_fetch
            return albums, finished
        albums = self._fetch_until_all_items_returned(my_album_fetcher)
        return self.get_albums(albums)

    def get_tracks(self, tracks):
        def track_fetcher(tracks):
            track_ids = [
                track.spotify_id
                for track in tracks
                if track.on_spotify()
            ]
            spotify_tracks = self.client.tracks(track_ids)["tracks"]
            return [
                Track.from_spotify_track(track)
                for track in spotify_tracks
            ]
        return self._fetch_in_batches(tracks, track_fetcher)

    def get_albums(self, albums):
        return self._get_albums_from_ids([album.spotify_id for album in albums])

    def _get_albums_from_ids(self, album_ids):
        def album_fetcher(album_ids):
            results = self.client.albums([
                album_id
                for album_id in album_ids
            ])
            return results['albums']
        albums = self._fetch_in_batches(album_ids, album_fetcher)
        return [
            Album.from_spotify_album(album)
            for album in albums
        ]

    def get_albums_of_tracks(self, tracks):
        "Returns list of albums that the tracks belong to. Duplicates excluded."
        album_ids = list({track.spotify_album_id for track in tracks})
        return self._get_albums_from_ids(album_ids)

    def create_playlist(self, name, description):
        user_id = self._get_current_user_id()
        playlist = self.client.user_playlist_create(
            user_id, name, public=False, description=description)
        return Playlist.from_spotify_playlist(playlist)

    def add_tracks(self, playlist, tracks):
        num_tracks_added_so_far, num_tracks_to_add = 0, len(tracks)
        while num_tracks_added_so_far < num_tracks_to_add:
            num_items_left_to_fetch = num_tracks_to_add - num_tracks_added_so_far
            batch_size = num_items_left_to_fetch if num_items_left_to_fetch <= SPOTIFY_ADD_TRACKS_TO_PLAYLIST_API_LIMIT else SPOTIFY_ADD_TRACKS_TO_PLAYLIST_API_LIMIT
            tracks_to_add = tracks[num_tracks_added_so_far:num_tracks_added_so_far+batch_size]
            self.client.user_playlist_add_tracks(
                self._get_current_user_id(),
                playlist.spotify_id,
                [track.spotify_id for track in tracks_to_add],
            )
            num_tracks_added_so_far += batch_size

    def add_track_at_position(self, playlist, track, position):
        self.client.user_playlist_add_tracks(
            self._get_current_user_id(),
            playlist.spotify_id,
            [track.spotify_id],
            position=position,
        )

    def remove_tracks_from_playlist(self, playlist, tracks):
        self.client.playlist_remove_all_occurrences_of_items(
            playlist.spotify_id, [track.spotify_id for track in tracks])

    def set_track_audio_features(self, tracks):
        """
        Returns:
            (dict): key (Track), value (AudioFeatures).
        """
        def audio_feature_fetcher(tracks):
            spotify_audio_features = self.client.audio_features([
                track.spotify_id
                for track in tracks
                if track.on_spotify()
            ])
            spotify_audio_features_by_track_id = {
                audio_features['id']: AudioFeatures.from_spotify_audio_features(audio_features)
                for audio_features in spotify_audio_features
            }
            for track in tracks:
                track.set_audio_features(
                    spotify_audio_features_by_track_id[track.spotify_id])
            return []
        self._fetch_in_batches(tracks, audio_feature_fetcher)

    def get_recommendations_based_on_tracks(self, tracks, song_attribute_ranges):
        """
        Params:
            tracks_ids ([str]): max length is 5.
            song_attribute_ranges (SongAttributeRanges).

        Returns:
            ([Track]).
        """
        if len(tracks) > RECOMMENDATION_SEED_LIMIT:
            tracks = tracks[:RECOMMENDATION_SEED_LIMIT]

        results = self.client.recommendations(
            seed_tracks=[track.spotify_id for track in tracks],
            limit=RECOMMENDATIONS_LIMIT,
            min_danceability=song_attribute_ranges.danceability_range[0],
            max_danceability=song_attribute_ranges.danceability_range[1],
            min_energy=song_attribute_ranges.energy_range[0],
            max_energy=song_attribute_ranges.energy_range[1],
            min_loudness=song_attribute_ranges.loudness_range[0],
            max_loudness=song_attribute_ranges.loudness_range[1],
            min_speechiness=song_attribute_ranges.speechiness_range[0],
            max_speechiness=song_attribute_ranges.speechiness_range[1],
            min_acousticness=song_attribute_ranges.acousticness_range[0],
            max_acousticness=song_attribute_ranges.acousticness_range[1],
            min_instrumentalness=song_attribute_ranges.instrumentalness_range[0],
            max_instrumentalness=song_attribute_ranges.instrumentalness_range[1],
            min_liveness=song_attribute_ranges.liveness_range[0],
            max_liveness=song_attribute_ranges.liveness_range[1],
            min_valence=song_attribute_ranges.valence_range[0],
            max_valence=song_attribute_ranges.valence_range[1],
            min_tempo=int(song_attribute_ranges.tempo_range[0]),
            max_tempo=int(song_attribute_ranges.tempo_range[1]),
            min_duration_ms=int(song_attribute_ranges.duration_ms_range[0]),
            max_duration_ms=int(song_attribute_ranges.duration_ms_range[1]),
            min_popularity=song_attribute_ranges.popularity_range[0],
            max_popularity=song_attribute_ranges.popularity_range[1],
        )
        return [
            Track.from_spotify_track(track)
            for track in results['tracks']
        ]

    def get_recommendation_seed_limit(self):
        return RECOMMENDATION_SEED_LIMIT

    def _get_playlist_tracks(self, playlist_id):
        def track_fetcher(offset=0):
            results = self.client.playlist_tracks(
                playlist_id, offset=offset)
            finished = len(results['items']) + offset >= results['total']
            tracks = [
                Track.from_spotify_playlist_track(track)
                for track in results['items']
            ]
            return tracks, finished

        return self._fetch_until_all_items_returned(track_fetcher)

    def _fetch_until_all_items_returned(self, fetch_func):
        """Skips duplicates that Spotify returns for some reason.

        Params:
            fetch_func (func): optional param 'offset',
                returning a 2-tuple where:
                - (List) the fetched items
                - (bool) whether fetching has finished

        Returns:
            (List): all fetched items.
        """
        all_items, finished = fetch_func()
        all_items = set(all_items)
        offset, batch_size = 0, API_BATCH_SIZE
        while not finished:
            offset += batch_size
            items, finished = fetch_func(offset=offset)
            all_items |= set(items)
        return list(all_items)

    def _fetch_in_batches(self, items_to_fetch, fetch_items):
        """
        Params:
            items_to_fetch ([Track|Album|Playlist]): sole argument for fetch_items.
            fetch_items (func): takes [str], returns list of items.
        """
        batch_size = min(API_BATCH_SIZE, len(items_to_fetch))
        fetched_items = []
        for batch_start_index in range(0, len(items_to_fetch), batch_size):
            batch_end_index = min(batch_start_index+batch_size, len(items_to_fetch))
            fetched_items.extend(
                fetch_items(items_to_fetch[batch_start_index:batch_end_index]))
        return fetched_items

    def _get_current_user_id(self):
        return self.client.me()['id']