from collections import defaultdict
from re import match

from app.models.recommendation_criteria import RecommendationCriteria


class MusicUtil:
    def __init__(self, spotify_client_wrapper):
        self.spotify_client_wrapper = spotify_client_wrapper

    def _add_artist_genres(self, albums):
        """
        Params:
            albums ([Album]).

        Returns:
            albums_by_id (dict):
                key (string): album ID.
                value (Album).
        """
        albums_by_id = dict()
        for album in albums:
            artist_ids = [artist.id for artist in album.artists]
            genres = list(set([
                genre
                for artist_id in artist_ids
                for genre in self.spotify_client_wrapper.get_artist_genres(artist_id)
            ]))
            album.set_genres(genres)
            albums_by_id[album.id] = album
        return albums_by_id

    def _detect_genre_matches(self, albums_by_id):
        adjacencies, genre_to_albums = defaultdict(lambda: defaultdict(list)), defaultdict(set)
        for _, album in albums_by_id.items():
            for genre in album.genres:
                for matching_album_id in genre_to_albums[genre]:
                    adjacencies[album.id][matching_album_id].append(genre)
                    adjacencies[matching_album_id][album.id].append(genre)
                genre_to_albums[genre].add(album.id)
        return adjacencies

    def _as_readable_key(self, list_):
        list_.sort()
        return ", ".join(list_) if len(list_) > 0 else "unknown"

    def _group_each_album_by_itself(self, album_ids):
        """
        Returns:
            ([dict]):
                e.g. [{
                    'album ids': {'3tb57GFYfkABviRejjp1lh'},
                    'genres': {'rock', 'punk'}
                }].
        """
        genres_by_album_ids = self.get_genres_by_album_ids(list(album_ids))
        return [
            {
                "album ids": {album_id},
                "genres": set(genres)
            }
            for album_id, genres in genres_by_album_ids.items()
        ]

    def _group_albums(self, album_ids, genre_matches):
        """
        Returns:
            grouped_albums ([dict]):
                e.g. [{
                    'album ids': {'3tb57GFYfkABviRejjp1lh'},
                    'genres': {'rock', 'punk'}
                }].
        """
        if len(album_ids) == 0 or len(genre_matches) == 0:
            return self._group_each_album_by_itself(album_ids)

        grouped_albums = defaultdict(lambda: defaultdict(set))
        for album_id in album_ids:
            for matching_album_id, genres_matched_on in genre_matches[album_id].items():
                group_key = self._as_readable_key(genres_matched_on)
                grouped_albums[group_key]["album ids"].add(album_id)
                grouped_albums[group_key]["album ids"].add(matching_album_id)
                grouped_albums[group_key]["genres"] = genres_matched_on
        return list(grouped_albums.values())

    def get_genres_by_album_ids(self, album_ids):
        "album_ids ([str]) -> genres_by_album_id (dict) with key (str) album ID, value ([str]) genres"
        genres_by_album_ids = defaultdict(list)
        for album in self.spotify_client_wrapper.get_albums(album_ids):
            for artist in album.artists:
                genres_by_album_ids[album.id].extend(
                    self.spotify_client_wrapper.get_artist_genres(artist.id))
        return genres_by_album_ids

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
                "genres": list(group['genres']),
                "albums": [albums_by_id[album_id] for album_id in group["album ids"]]
            }
            for group in album_groups
            if len(group["genres"]) >= min_genres_per_group
        ]

    def get_most_popular_tracks(self, album, num_tracks):
        # get track popularity all together in one call
        self.populate_popularity_if_absent(album.tracks)
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
        return self.get_most_popular_first(album.tracks)

    def get_most_popular_first(self, tracks):
        self.populate_popularity_if_absent(tracks)
        return sorted(
            tracks,
            key=lambda track: track.popularity,
            reverse=True
        )

    def populate_popularity_if_absent(self, tracks):
        track_uris_popularity_missing, track_index_by_uri = [], {}
        for index, track in enumerate(tracks):
            track_index_by_uri[track.uri] = index
            if track.popularity is None:
                track_uris_popularity_missing.append(track.uri)
        if len(track_uris_popularity_missing) == 0:
            return

        tracks_w_popularity = self.spotify_client_wrapper.get_tracks(
            track_uris_popularity_missing)
        for track in tracks_w_popularity:
            index = track_index_by_uri[track.uri]
            tracks[index].popularity = track.popularity

    def get_most_popular_artist(self, artists):
        """
        Params:
            artists ([Artist]).
        """
        if len(artists) == 0:
            return None

        most_popular_artist = artists[0]
        for artist in artists[1:]:
            if artist.popularity > most_popular_artist.popularity:
                most_popular_artist = artist
        return most_popular_artist

    def get_albums_as_readable_list(self, albums):
        """
        Params:
            albums ([Album]).

        Returns:
            (str): e.g. "- Bringing It All Back Home by Bob Dylan"
        """
        artist_names_to_str = lambda artists: ', '.join([artist.name for artist in artists])
        return '\n'.join([
            f"- {album.name} by {artist_names_to_str(album.artists)}"
            for album in albums
        ])

    def get_album_ids(self, tracks):
        return list(set([track.album_id for track in tracks]))

    def get_common_genres_in_playlist(self, spotify_playlist_id):
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

    def get_artist_ids(self, spotify_playlist_id):
        "spotify_playlist_id (str) -> [set] where each element is an artist id (str)"
        playlist = self.spotify_client_wrapper.get_playlist(spotify_playlist_id)
        return list({
            artist.id
            for track in playlist.tracks
            for artist in track.artists
        })

    def order_albums_chronologically(self, albums):
        return sorted(albums, key=lambda album: album.release_date)

    def get_discography(self, artist):
        return self.spotify_client_wrapper.get_artist_albums(artist.id)

    def is_live(self, album):
        # '(?i)' is a flag that enables cap insensitivity
        # '[\(\[]' and '[\)\]]' are opening and closing braces; e.g. (Live), [Live]
        regular_expression = "(?i).*[\(\[]live[\)\]].*"
        return match(regular_expression, album.name) is not None

    def is_a_bootleg(self, album):
        # '(?i)' is a flag that enables cap insensitivity
        # '([^a-z]|$)' means that either there is a non-alphabetical char or string ends
        # 's?' means bootleg may be plural
        # the expression aims to match the isolated word "bootleg"
        # avoiding substring matches e.g. as in "bootleggers"
        regular_expression = "(?i).*[^a-z]bootlegs?([^a-z]|$).*"
        return match(regular_expression, album.name) is not None

    def is_a_demo(self, album):
        # '(?i)' is a flag that enables cap insensitivity
        # '([^a-z]|$)' means that either there is a non-alphabetical char or string ends
        # 's?' means demo may be plural
        # the expression aims to match the isolated word "demo"
        # avoiding substring matches e.g. as in "demon"
        regular_expression = "(?i).*[^a-z]demos?([^a-z]|$).*"
        return match(regular_expression, album.name) is not None

    def filter_out_demos_bootlegs_and_live_albums(self, albums):
        return [
            album
            for album in albums
            if (
                not self.is_a_demo(album) and
                not self.is_a_bootleg(album) and
                not self.is_live(album)
            )
        ]

    def _strip_metadata_in_parentheses_or_brackets(self, album_name):
        """(Parentheses) and [Brackets]
        Assumptions:
            - Parentheses contain metadata depending on where they occur
                - If parentheses occur at the beginning of name, they don't contain metadata
                - Otherwise, they contain metadata
            - If at all, only 1 set of parentheses occurs
            - Parentheses are balanced
            - All of the above, applied also to [brackets]
        """
        without_parenthesized_substring = self._strip_metadata_between(
            album_name.strip(), "(", ")")
        return self._strip_metadata_between(
            without_parenthesized_substring, "[", "]")

    def _strip_metadata_between(self, str_, opening_token, closing_token):
        if opening_token in str_:
            open_paren_idx = str_.index(closing_token)
            if open_paren_idx > 0:
                tokens = str_.split(opening_token)
                str_ = tokens[0].strip()
        return str_

    def is_same_album_name(self, album_name_1, album_name_2):
        return self._normalize_album_name(album_name_1) == self._normalize_album_name(album_name_2)

    def _normalize_album_name(self, album_name):
        return self._strip_metadata_in_parentheses_or_brackets(
                album_name.strip().lower())

    def filter_out_duplicates(self, albums, album_tie_breaker):
        albums_by_name = dict()
        for album in albums:
            normalized_album_name = self._normalize_album_name(album.name)
            if normalized_album_name in albums_by_name:
                albums_by_name[normalized_album_name] = album_tie_breaker(
                    album, albums_by_name[normalized_album_name])
            else:
                albums_by_name[normalized_album_name] = album
        return albums_by_name.values()

    def filter_out_duplicates_demos_and_live_albums(self, albums):
        albums = self.filter_out_demos_bootlegs_and_live_albums(albums)
        def prefer_most_popular(album1, album2):
            return album1 if album1.popularity > album2.popularity else album2
        return self.filter_out_duplicates(albums, prefer_most_popular)

    def get_album_by_artist(self, album_name, artist):
        "Returns list of matching albums"
        matching_artists = self.spotify_client_wrapper.get_matching_artists(artist)
        artist = self.get_most_popular_artist(matching_artists)
        albums = self.spotify_client_wrapper.get_artist_albums(artist.id)
        return [
            album
            for album in albums
            if self.is_same_album_name(album_name, album.name)
        ]

    def populate_track_audio_features(self, playlist):
        """Fetches and sets track.audio_features for each track in the playlist.

        Params:
            playlist (Playlist).
        """
        audio_features_by_track_ids = self.spotify_client_wrapper.get_audio_features_by_track_id([
            track.uri
            for track in playlist.tracks
            if track.audio_features is None
        ])
        for track in playlist.tracks:
            if track.id in audio_features_by_track_ids:
                track.set_audio_features(
                    audio_features_by_track_ids[track.id])

    def get_recommendations_based_on_tracks(self, track_ids, num_recommendations, recommendation_criteria):
        """
        Params:
            tracks_ids ([str]): max length is 5.
            num_recommendations (int): max is 100.
            recommendation_criteria (RecommendationCriteria).
        """
        recommendations_with_count = self._get_recommendations_based_on_tracks_in_batches(
            track_ids, recommendation_criteria)
        print(f"Found {len(recommendations_with_count)} recommendations.")
        most_recommended_tracks = sorted(
            list(recommendations_with_count.items()),
            key=lambda track_count_tuple: track_count_tuple[1],
            reverse=True,
        )
        print(f"Whittled down to {len(recommendations_with_count)} recommendations.")
        num_recommendations = min(num_recommendations, len(most_recommended_tracks))
        return [
            track_count_tuple[0]
            for track_count_tuple in most_recommended_tracks[:num_recommendations]
        ]

    def make_recommendation_criteria(self, audio_features_min, audio_features_max, popularity_min, popularity_max):
        """
        Params:
            audio_features_min (AudioFeatures).
            audio_features_max (AudioFeatures).
            popularity_min (int): in [0, 100].
            popularity_max (int): in [0, 100].
        """
        recommendation_criteria = RecommendationCriteria.from_audio_features_min_max_ranges(
            audio_features_min, audio_features_max)
        recommendation_criteria.set_popularity_min_max_range(
            popularity_min, popularity_max)
        return recommendation_criteria

    def _get_recommendations_based_on_tracks_in_batches(self, track_ids, recommendation_criteria):
        """
        Params:
            tracks_ids ([str]): max length is 5.
            recommendation_criteria (RecommendationCriteria).

        Returns:
            recommendations_with_count (dict):
        """
        recommendation_limit = self.spotify_client_wrapper.get_recommendation_seed_limit()
        recommendations_with_count = defaultdict(int)
        for min_index in range(0, len(track_ids), recommendation_limit):
            max_index = min(min_index+recommendation_limit, len(track_ids))
            recommendations = self.spotify_client_wrapper.get_recommendations_based_on_tracks(
                track_ids[min_index:max_index], recommendation_criteria)
            for track in recommendations:
                if track.id not in track_ids:
                    recommendations_with_count[track] += 1
        return recommendations_with_count