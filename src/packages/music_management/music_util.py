from collections import defaultdict
from re import match
from packages.music_api_clients.models.audio_features import AudioFeatures
from packages.music_api_clients.models.song_attribute_ranges import SongAttributeRanges


class MusicUtil:
    def __init__(self, music_api_client, info_logger):
        self.music_api_client = music_api_client
        self.info_logger = info_logger

    def get_genres_by_album_ids(self, album_ids):
        "album_ids ([str]) -> genres_by_album_id (dict) with key (str) album ID, value ([str]) genres"
        genres_by_album_ids = defaultdict(list)
        for album in self.music_api_client.get_albums(album_ids):
            for artist in album.artists:
                genres_by_album_ids[album.spotify_id].extend(
                    self.music_api_client.get_artist_genres(artist.spotify_id))
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
            track_index_by_uri[track.spotify_uri] = index
            if track.popularity is None:
                track_uris_popularity_missing.append(track.spotify_uri)
        if len(track_uris_popularity_missing) == 0:
            return

        tracks_w_popularity = self.music_api_client.get_tracks(
            track_uris_popularity_missing)
        for track in tracks_w_popularity:
            index = track_index_by_uri[track.spotify_uri]
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
        return list(set([track.spotify_album_id for track in tracks]))

    def get_common_genres_in_playlist(self, spotify_playlist_id):
        playlist = self.music_api_client.get_playlist(spotify_playlist_id)
        genres_in_common = set()
        for track in playlist.get_tracks():
            genres = self.get_genres([
                artist.spotify_id
                for artist in track.artists
            ])
            if len(genres_in_common) == 0:
                genres_in_common = genres
            else:
                genres_in_common &= genres
        return list(genres_in_common)

    def get_genres(self, artist_ids):
        all_genres = set()
        for artist_id in artist_ids:
            artist_genres = self.music_api_client.get_artist_genres(artist_id)
            all_genres |= set(artist_genres)
        return all_genres

    def get_highly_common_genres(self, playlist_id):
        """
        Params:
            playlist_id (str).

        Returns:
            genres ([str]).
        """
        genres, top_percentages = [], [10, 20, 30, 40, 50]
        for top_percentage in top_percentages:
            genres = self.get_most_common_genres(playlist_id, top_percentage)
            if len(genres) > 0:
                break
        if len(genres) == 0:
            self.info_logger("Couldn't find any genres :(")
            return []
        self.info_logger(f"Your playlist's most common genres are: {', '.join(genres)}")
        return genres

    def get_most_common_genres(self, playlist_id, top_percent):
        """Get top x% most common genres, or single most common one.

        Params:
            playlist_id (str).
            top_percent (int): [1, 100].

        Returns:
            genres ([str]).
        """
        target_genres = self.get_genres_by_frequency(playlist_id)
        target_genres_list = [(genre, count) for genre, count in target_genres.items()]
        target_genres_list.sort(key=lambda pair: pair[1], reverse=True)
        genres_in_top_percent = max(int(len(target_genres_list)/top_percent), 1)
        return [genre for genre, _ in target_genres_list[:genres_in_top_percent]]

    def get_genres_by_frequency(self, spotify_playlist_id):
        """
        Returns:
            (dict): key (str) genre, value (int) count.
        """
        genre_count = defaultdict(int)
        for artist_id in self.get_artist_ids(spotify_playlist_id):
            genres = self.music_api_client.get_artist_genres(artist_id)
            for genre in genres:
                genre_count[genre] += 1
        return dict(genre_count)

    def get_artist_ids(self, spotify_playlist_id):
        "spotify_playlist_id (str) -> [set] where each element is an artist id (str)"
        playlist = self.music_api_client.get_playlist(spotify_playlist_id)
        return list({
            artist.spotify_id
            for track in playlist.get_tracks()
            for artist in track.artists
        })

    def order_albums_chronologically(self, albums):
        return sorted(albums, key=lambda album: album.release_date)

    def get_discography(self, artist):
        return self.music_api_client.get_artist_albums(artist.spotify_id)

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

    def is_same_album_name(self, album_name_1, album_name_2):
        return self._normalize_album_name(album_name_1) == self._normalize_album_name(album_name_2)

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

    def filter_out_if_not_in_albums(self, tracks, albums):
        album_ids = [album.spotify_id for album in albums]
        return [
            track
            for track in tracks
            if track.spotify_album_id in album_ids
        ]

    def get_album_by_artist(self, album_name, artist):
        "Returns list of matching albums"
        matching_artists = self.music_api_client.get_matching_artists(artist)
        artist = self.get_most_popular_artist(matching_artists)
        albums = self.music_api_client.get_artist_albums(artist.spotify_id)
        return [
            album
            for album in albums
            if self.is_same_album_name(album_name, album.name)
        ]

    def get_albums_in_playlist(self, playlist):
        "Returns list of unique album IDs."
        album_ids =  list({
            track.spotify_album_id
            for track in playlist.get_tracks()
        })
        return self.music_api_client.get_albums(album_ids)

    def populate_track_audio_features(self, playlist):
        """Fetches and sets track.audio_features for each track in the playlist.

        Params:
            playlist (Playlist).
        """
        audio_features_by_track_ids = self.music_api_client.get_audio_features_by_track_id([
            track.spotify_uri
            for track in playlist.get_tracks()
            if track.audio_features is None
        ])
        for track in playlist.get_tracks():
            if track.spotify_id in audio_features_by_track_ids:
                track.set_audio_features(
                    audio_features_by_track_ids[track.spotify_id])

    def get_recommendations_based_on_tracks(self, track_ids, song_attribute_ranges):
        """
        Params:
            tracks_ids ([str]): max length is 5.
            song_attribute_ranges (SongAttributeRanges).

        Returns:
            recommended_tracks_by_percentage (dict): key (float) percentage, in [0,1],
                value ([Track]) recommended tracks.
        """
        recommendations_by_percent = self._get_recommendations_based_on_tracks_in_batches(
            track_ids, song_attribute_ranges)
        recommended_tracks_by_percentage = defaultdict(list)
        for track, percentage_recommended in recommendations_by_percent.items():
            recommended_tracks_by_percentage[percentage_recommended].append(track)
        return recommended_tracks_by_percentage

    def get_strict_song_attribute_ranges(self, playlist, playlist_stats):
        """
        Params:
            playlist (Playlist).
            playlist_stats (PlaylistStats).
        """
        audio_features_min, audio_features_max = playlist_stats.get_audio_feature_representative_range(playlist)
        popularity_min, popularity_max = playlist_stats.get_popularity_representative_range(playlist)
        song_attribute_ranges = SongAttributeRanges.from_audio_features_min_max_ranges(
            audio_features_min, audio_features_max)
        song_attribute_ranges.set_popularity_min_max_range(
            popularity_min, popularity_max)
        return song_attribute_ranges

    def get_lenient_song_attribute_ranges(self, playlist):
        audio_features_min, audio_features_max = self.get_min_and_max_audio_features(playlist)
        popularity_min, popularity_max = self.get_min_and_max_popularity(playlist)
        song_attribute_ranges = SongAttributeRanges.from_audio_features_min_max_ranges(
            audio_features_min, audio_features_max)
        song_attribute_ranges.set_popularity_min_max_range(
            popularity_min, popularity_max)
        return song_attribute_ranges

    def get_min_and_max_popularity(self, playlist):
        popularities = [track.popularity for track in playlist.get_tracks()]
        return min(popularities), max(popularities)

    def get_min_and_max_audio_features(self, playlist):
        min_audio_features = AudioFeatures.with_maximum_values()
        max_audio_features = AudioFeatures.with_minimum_values()
        for track in playlist.get_tracks():
            if track.audio_features.danceability < min_audio_features.danceability:
                min_audio_features.danceability = track.audio_features.danceability
            if track.audio_features.danceability > max_audio_features.danceability:
                max_audio_features.danceability = track.audio_features.danceability
            if track.audio_features.energy < min_audio_features.energy:
                min_audio_features.energy = track.audio_features.energy
            if track.audio_features.energy > max_audio_features.energy:
                max_audio_features.energy = track.audio_features.energy
            if track.audio_features.key < min_audio_features.key:
                min_audio_features.key = track.audio_features.key
            if track.audio_features.key > max_audio_features.key:
                max_audio_features.key = track.audio_features.key
            if track.audio_features.loudness < min_audio_features.loudness:
                min_audio_features.loudness = track.audio_features.loudness
            if track.audio_features.loudness > max_audio_features.loudness:
                max_audio_features.loudness = track.audio_features.loudness
            if track.audio_features.mode < min_audio_features.mode:
                min_audio_features.mode = track.audio_features.mode
            if track.audio_features.mode > max_audio_features.mode:
                max_audio_features.mode = track.audio_features.mode
            if track.audio_features.speechiness < min_audio_features.speechiness:
                min_audio_features.speechiness = track.audio_features.speechiness
            if track.audio_features.speechiness > max_audio_features.speechiness:
                max_audio_features.speechiness = track.audio_features.speechiness
            if track.audio_features.acousticness < min_audio_features.acousticness:
                min_audio_features.acousticness = track.audio_features.acousticness
            if track.audio_features.acousticness > max_audio_features.acousticness:
                max_audio_features.acousticness = track.audio_features.acousticness
            if track.audio_features.instrumentalness < min_audio_features.instrumentalness:
                min_audio_features.instrumentalness = track.audio_features.instrumentalness
            if track.audio_features.instrumentalness > max_audio_features.instrumentalness:
                max_audio_features.instrumentalness = track.audio_features.instrumentalness
            if track.audio_features.liveness < min_audio_features.liveness:
                min_audio_features.liveness = track.audio_features.liveness
            if track.audio_features.liveness > max_audio_features.liveness:
                max_audio_features.liveness = track.audio_features.liveness
            if track.audio_features.valence < min_audio_features.valence:
                min_audio_features.valence = track.audio_features.valence
            if track.audio_features.valence > max_audio_features.valence:
                max_audio_features.valence = track.audio_features.valence
            if track.audio_features.tempo < min_audio_features.tempo:
                min_audio_features.tempo = track.audio_features.tempo
            if track.audio_features.tempo > max_audio_features.tempo:
                max_audio_features.tempo = track.audio_features.tempo
            if track.audio_features.duration_ms < min_audio_features.duration_ms:
                min_audio_features.duration_ms = track.audio_features.duration_ms
            if track.audio_features.duration_ms > max_audio_features.duration_ms:
                max_audio_features.duration_ms = track.audio_features.duration_ms
            if track.audio_features.time_signature < min_audio_features.time_signature:
                min_audio_features.time_signature = track.audio_features.time_signature
            if track.audio_features.time_signature > max_audio_features.time_signature:
                max_audio_features.time_signature = track.audio_features.time_signature
        return min_audio_features, max_audio_features

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
            artist_ids = [artist.spotify_id for artist in album.artists]
            genres = list(set([
                genre
                for artist_id in artist_ids
                for genre in self.music_api_client.get_artist_genres(artist_id)
            ]))
            album.set_genres(genres)
            albums_by_id[album.spotify_id] = album
        return albums_by_id

    def _detect_genre_matches(self, albums_by_id):
        adjacencies, genre_to_albums = defaultdict(lambda: defaultdict(list)), defaultdict(set)
        for _, album in albums_by_id.items():
            for genre in album.genres:
                for matching_album_id in genre_to_albums[genre]:
                    adjacencies[album.spotify_id][matching_album_id].append(genre)
                    adjacencies[matching_album_id][album.spotify_id].append(genre)
                genre_to_albums[genre].add(album.spotify_id)
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
        stripped_str = str_[:]
        if opening_token in stripped_str:
            open_token_idx = stripped_str.index(opening_token)
            stripped_str = stripped_str[:open_token_idx]
        if closing_token in stripped_str:
            closing_token_index = stripped_str.index(closing_token)
            stripped_str = stripped_str[closing_token_index+1:]
        stripped_str = stripped_str.strip()
        return stripped_str if len(stripped_str) > 0 else str_

    def _normalize_album_name(self, album_name):
        return self._strip_metadata_in_parentheses_or_brackets(
                album_name.strip().lower())

    def _get_recommendations_based_on_tracks_in_batches(self, track_ids, song_attribute_ranges):
        """
        Params:
            tracks_ids ([str]): max length is 5.
            song_attribute_ranges (SongAttributeRanges).

        Returns:
            (dict): key (Track), value (float) in [0,1].
        """
        recommendation_limit = self.music_api_client.get_recommendation_seed_limit()
        recommendations_with_count, num_batches = defaultdict(int), 0
        for min_index in range(0, len(track_ids), recommendation_limit):
            num_batches += 1
            max_index = min(min_index+recommendation_limit, len(track_ids))
            recommendations = self.music_api_client.get_recommendations_based_on_tracks(
                track_ids[min_index:max_index], song_attribute_ranges)
            for track in recommendations:
                if track.spotify_id not in track_ids:
                    recommendations_with_count[track] += 1
        return {
            track: float(count)/num_batches
            for track, count in recommendations_with_count.items()
        }

    def get_num_diff_artists(self, albums):
        return len({
            artist.spotify_id
            for album in albums
            for artist in album.artists
        })