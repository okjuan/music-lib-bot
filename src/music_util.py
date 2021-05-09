from collections import defaultdict

from models.album import Album


class MusicUtil:
    def __init__(self, spotify_client_wrapper):
        self.spotify_client_wrapper = spotify_client_wrapper

    def _add_artist_genres(self, albums):
        albums_by_id = dict()
        for album in albums:
            artist_ids = [artist['id'] for artist in album['artists']]
            album['genres'] = [
                genre
                for artist_id in artist_ids
                for genre in self.spotify_client_wrapper.get_artist_genres(artist_id)
            ]
            albums_by_id[album['id']] = album
        return albums_by_id

    def _detect_genre_matches(self, albums_by_id):
        adjacencies, genre_to_albums = defaultdict(lambda: defaultdict(list)), defaultdict(set)
        for _, album in albums_by_id.items():
            for genre in album['genres']:
                for matching_album_id in genre_to_albums[genre]:
                    adjacencies[album['id']][matching_album_id].append(genre)
                    adjacencies[matching_album_id][album['id']].append(genre)
                genre_to_albums[genre].add(album['id'])
        return adjacencies

    def _as_readable_key(self, list_):
        list_.sort()
        return ", ".join(list_) if len(list_) > 0 else "unknown"

    def _group_albums(self, album_ids, genre_matches):
        """
        Returns:
            grouped_albums ([dict]):
                e.g. [{
                    'album ids': {'3tb57GFYfkABviRejjp1lh'},
                    'genres': ['rock', 'punk']
                }].
        """
        if len(album_ids) == 0 or len(genre_matches) == 0:
            return [
                {
                    "album ids": [album_id],
                    "genres": self.get_genres_in_album(album_id)
                }
                for album_id in album_ids
            ]

        grouped_albums = dict()
        for album_id in album_ids:
            for matching_album_id, genres_matched_on in genre_matches[album_id].items():
                group_key = self._as_readable_key(genres_matched_on)
                if group_key not in grouped_albums:
                    grouped_albums[group_key] = {
                        "album ids": set(),
                        "genres": genres_matched_on
                    }
                grouped_albums[group_key]["album ids"].add(album_id)
                grouped_albums[group_key]["album ids"].add(matching_album_id)
        return [group for _, group in grouped_albums.items()]

    def group_albums_by_genre(self, albums, min_genres_per_group):
        """
        Returns:
            albums_by_genre ([dict]):
                e.g. [{genres: ['rock', 'dance rock'], albums: [Album]}]
        """
        albums_by_id = self._add_artist_genres(albums)
        genre_matches = self._detect_genre_matches(albums_by_id)
        album_groups = self._group_albums(albums_by_id.keys(), genre_matches)
        return [
            {
                "genres": group['genres'],
                "albums": [albums_by_id[album_id] for album_id in group["album ids"]]
            }
            for group in album_groups
            if len(group["genres"]) >= min_genres_per_group
        ]

    def get_most_popular_tracks(self, album, num_tracks):
        all_tracks = self.get_tracks_most_popular_first(album)
        return all_tracks[:min(num_tracks, len(all_tracks))]

    def get_most_popular_tracks_from_each(self, albums, num_tracks_per_album):
        tracks = [
            track
            for album in albums
            for track in self.get_most_popular_tracks(album, num_tracks_per_album)
        ]
        return tracks

    def get_tracks_most_popular_first(self, album):
        tracks_w_metadata = [
            self.spotify_client_wrapper.get_track(track['uri'])
            for track in album['tracks']['items']
        ]
        return sorted(
            tracks_w_metadata,
            key=lambda track: track.popularity,
            reverse=True
        )

    def get_albums_as_readable_list(self, albums):
        artist_names_to_str = lambda artists: ', '.join([artist['name'] for artist in artists])
        return '\n'.join([
            f"- {album['name']} by {artist_names_to_str(album['artists'])}"
            for album in albums
        ])

    def get_albums(self, tracks):
        return list(set([track.album for track in tracks]))

    def get_genres_in_playlist(self, spotify_playlist_id):
        artist_ids = self.get_artist_ids(spotify_playlist_id)
        if len(artist_ids) == 0:
            return []

        genres_in_common = set(self.spotify_client_wrapper.get_artist_genres(artist_ids[0]))
        for artist_id in artist_ids[1:]:
            genres = set(self.spotify_client_wrapper.get_artist_genres(artist_id))
            genres_in_common &= genres
        return list(genres_in_common)

    def get_genres_by_frequency(self, spotify_playlist_id):
        genre_count = defaultdict(int)
        for artist_id in self.get_artist_ids(spotify_playlist_id):
            genres = self.spotify_client_wrapper.get_artist_genres(artist_id)
            for genre in genres:
                genre_count[genre] += 1
        return dict(genre_count)

    def get_genres_in_album(self, album_id):
        genres = []
        for artist in self.spotify_client_wrapper.get_album(album_id).artists:
            genres.extend(self.spotify_client_wrapper.get_artist_genres(artist['id']))
        return genres

    def get_artist_ids(self, spotify_playlist_id):
        playlist = self.spotify_client_wrapper.get_playlist(spotify_playlist_id)
        return list({
            artist['id']
            for track in playlist.tracks
            for artist in track.artists
        })