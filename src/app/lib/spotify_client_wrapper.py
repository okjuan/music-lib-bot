from spotipy.oauth2 import SpotifyOAuth
import spotipy

from app.models.album import Album
from app.models.audio_features import AudioFeatures
from app.models.artist import Artist
from app.models.playlist import Playlist
from app.models.track import Track


API_BATCH_SIZE = 20
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

    def get_artist_genres(self, artist_id):
        return self.client.artist(artist_id)['genres']

    def get_artist_albums(self, artist_id):
        def album_fetcher(offset=0):
            results = self.client.artist_albums(
                artist_id, album_type="album", offset=offset)
            finished = len(results['items']) + offset >= results['total']
            return [album['id'] for album in results['items']], finished
        album_ids = self._fetch_until_all_items_returned(album_fetcher)
        return self.get_albums(album_ids)

    def get_my_albums(self, max_albums_to_fetch):
        def my_album_fetcher(offset=0):
            results = self.client.current_user_saved_albums(offset=offset)
            num_results = len(results['items'])
            items = results['items'][:min(num_results, max_albums_to_fetch)]
            albums = [item['album'] for item in items]
            finished = num_results + offset >= max_albums_to_fetch
            return [album['id'] for album in albums], finished
        album_ids = self._fetch_until_all_items_returned(my_album_fetcher)
        return self.get_albums(album_ids)

    def get_tracks(self, track_ids):
        def track_fetcher(track_ids):
            return self._fetch_by_track_ids(
                track_ids,
                lambda track_ids: self.client.tracks(track_ids)["tracks"]
            )
        tracks = self._fetch_in_batches(track_ids, track_fetcher)
        return [
            Track.from_spotify_track(track)
            for _, track in tracks
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

    def remove_tracks_from_playlist(self, playlist_id, track_uris):
        self.client.playlist_remove_all_occurrences_of_items(playlist_id, track_uris)

    def get_audio_features_by_track_id(self, track_ids):
        """
        Returns:
            (dict): key (str) track ID, value (AudioFeatures).
        """
        def audio_feature_fetcher(track_ids):
            return self._fetch_by_track_ids(
                track_ids, self.client.audio_features)
        all_audio_features = self._fetch_in_batches(
            track_ids, audio_feature_fetcher)
        return {
            track_id: AudioFeatures.from_spotify_audio_features(
                audio_features)
            if audio_features is not None else None
            for track_id, audio_features in all_audio_features
        }

    def on_spotify(self, track_id):
        return track_id[:13] != "spotify:local"

    def get_recommendations_based_on_tracks(self, track_ids, song_attribute_ranges):
        """
        Params:
            tracks_ids ([str]): max length is 5.
            song_attribute_ranges (SongAttributeRanges).

        Returns:
            ([Track]).
        """
        if len(track_ids) > RECOMMENDATION_SEED_LIMIT:
            track_ids = track_ids[:RECOMMENDATION_SEED_LIMIT]

        results = self.client.recommendations(
            seed_tracks=track_ids,
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

    def _fetch_in_batches(self, item_ids, fetch_items):
        """
        Params:
            item_ids ([str]): sole argument for fetch_items.
            fetch_items (func): takes [str], returns list of items.
        """
        batch_size = min(API_BATCH_SIZE, len(item_ids))
        fetched_items = []
        for batch_start_index in range(0, len(item_ids), batch_size):
            batch_end_index = min(batch_start_index+batch_size, len(item_ids))
            fetched_items.extend(
                fetch_items(item_ids[batch_start_index:batch_end_index]))
        return fetched_items

    def _get_current_user_id(self):
        return self.client.me()['id']

    def _fetch_by_track_ids(self, track_ids, fetcher):
        tracks_on_spotify, tracks_not_on_spotify = [], []
        for track_id in track_ids:
            if self.on_spotify(track_id):
                tracks_on_spotify.append(track_id)
            else:
                tracks_not_on_spotify.append(track_id)

        audio_features = fetcher(tracks_on_spotify)

        result_data = [
            (track_audio_features['id'], track_audio_features)
            for track_audio_features in audio_features
        ]
        result_data.extend([
            (track_id, None)
            for track_id in tracks_not_on_spotify
        ])
        return result_data