from collections import defaultdict
from re import match


class MusicUtil:
    def __init__(self, spotify_client_wrapper):
        self.spotify_client_wrapper = spotify_client_wrapper

    def _add_artist_genres(self, albums):
        albums_by_id = dict()
        for album in albums:
            artist_ids = [artist['id'] for artist in album.artists]
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
        return list(grouped_albums.values())

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
        # get track popularity all together in one call
        all_tracks = self._get_track_popularity_if_absent(album.tracks)
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
        tracks = self._get_track_popularity_if_absent(album.tracks)
        return sorted(
            tracks,
            key=lambda track: track.popularity,
            reverse=True
        )

    def _get_track_popularity_if_absent(self, tracks):
        tracks_with_popularity, track_uris_popularity_missing = [], []
        for track in tracks:
            if track.popularity is None:
                track_uris_popularity_missing.append(track.uri)
            else:
                tracks_with_popularity.append(track)
        if len(track_uris_popularity_missing) > 0:
            tracks_with_popularity.extend(
                self.spotify_client_wrapper.get_tracks(track_uris_popularity_missing))
        return tracks_with_popularity

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
        artist_names_to_str = lambda artists: ', '.join([artist['name'] for artist in artists])
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

    # TODO: replace with more concise regular expression implementation
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