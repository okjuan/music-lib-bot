class PlaylistUpdater:
    def __init__(self, my_music_lib, music_util, music_api_client, info_logger, playlist_analyzer):
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.music_api_client = music_api_client
        self.info_logger = info_logger
        self.playlist_analyzer = playlist_analyzer

    def create_or_update_all_targets_from_seeds(self, seed_playlists, num_tracks_per_album, get_target_playlist_name):
        """Creates or updates 'target' playlists with songs in source playlists, avoiding uplicates.
        Params:
            seed_playlists ([Playlist]).
            num_tracks_per_album (int).
            get_target_playlist_name ((Playlist) => (str)): param: seed playlist.

        Returns:
            updates ([(Playlist, int,)]): list of tuples: each consists of the target playlist and number of songs that were added to it.
        """
        updates = []
        for seed_playlist in seed_playlists:
            update = self.create_or_update_target_from_seed(
                seed_playlist,
                num_tracks_per_album,
                get_target_playlist_name,
            )
            updates += [update]
        return updates

    def create_or_update_target_from_seed(self, seed_playlist, num_tracks_per_album, get_target_playlist_name):
        """Creates or updates a 'target' playlist with songs in source playlist, avoiding duplicates!
        Params:
            seed_playlist (Playlist).
            num_tracks_per_album (int).
            get_target_playlist_name ((Playlist) => (str)): param: seed playlist.

        Returns:
            (Playlist, int,): target playlist and number of songs that were added to it.
        """
        target_playlist_name = get_target_playlist_name(seed_playlist)
        target_playlist = self.my_music_lib.get_or_create_playlist(target_playlist_name)
        if target_playlist.get_num_tracks() > 0:
            current_albums = self.music_util.get_albums_of_tracks(
                target_playlist.get_tracks())
        else:
            current_albums = []

        seed_albums = self.music_util.get_albums_of_tracks(seed_playlist.get_tracks())
        albums_to_add = set(seed_albums) - set(current_albums)

        if len(albums_to_add) == 0:
            return target_playlist, 0

        tracks_to_add = self.music_util.get_most_popular_tracks_from_each(
            albums_to_add, num_tracks_per_album)
        self.my_music_lib.add_tracks_in_random_positions(
            target_playlist, [track for track in tracks_to_add])
        return target_playlist, len(tracks_to_add)

    def add_tracks_from_my_saved_albums_with_same_genres(self, playlist, get_num_tracks_per_album, get_num_albums_to_fetch):
        "Returns (int) number of tracks added to playlist"
        tracks = self._get_tracks_from_my_saved_albums_with_same_genres(
            playlist, get_num_tracks_per_album, get_num_albums_to_fetch)

        if len(tracks) == 0:
            self.info_logger(f"Couldn't find any new tracks in your library with the same exact genres as your playlist '{playlist.name}'")
            return 0

        self.info_logger(f"Found {len(tracks)} tracks with exact same genres as those already in your playlist..")
        self.my_music_lib.add_tracks_in_random_positions(playlist, tracks)
        return len(tracks)

    def add_tracks_from_my_saved_albums_with_similar_genres(self, playlist, get_num_tracks_per_album, get_num_albums_to_fetch):
        """Less strict version of add_tracks_from_my_saved_albums_with_same_genres
        Returns:
            (int): number of tracks added to playlist.
        """
        tracks = self._get_tracks_from_my_saved_albums_with_similar_genres(
            playlist, get_num_tracks_per_album, get_num_albums_to_fetch)

        if len(tracks) == 0:
            self.info_logger(f"Couldn't find any new tracks in your library with similar genres as those your playlist '{playlist.name}'")
            return 0

        self.info_logger(f"Found {len(tracks)} tracks with similar genres to those already in your playlist..")
        self.my_music_lib.add_tracks_in_random_positions(playlist, tracks)
        return len(tracks)

    def add_recommended_songs_with_similar_attributes(self, playlist, get_num_songs_to_add):
        num_songs_added = self._add_recommended_songs_that_match_strict_criteria(
            playlist, get_num_songs_to_add)
        if num_songs_added > 0:
            return
        self.info_logger("Couldn't find recommendations... widening song attribute range")
        self._add_recommended_songs_that_match_lenient_criteria(
            playlist, get_num_songs_to_add)

    def add_recommended_songs(self, playlist, song_attribute_ranges, get_num_songs_to_add):
        """
        Params:
            song_attribute_ranges (SongAttributeRanges).
            get_num_songs_to_add (lambda): takes 0 params, returns int.
        Returns:
            (int): number of recommended songs added.
        """
        self.info_logger("Getting recommendations..")
        recommended_tracks_by_percentage = self.music_util.get_recommendations_based_on_tracks(
            playlist.get_tracks(), song_attribute_ranges)

        highly_recommended_tracks = []
        for recommended_percentage, recommended_tracks in recommended_tracks_by_percentage.items():
            if recommended_percentage < 0.5:
                self.info_logger(f"Ignoring {len(recommended_tracks)} recommendations because they're not highly recommended.")
            else:
                highly_recommended_tracks.extend(recommended_tracks)

        if len(highly_recommended_tracks) == 0:
            self.info_logger("Sorry, couldn't find recommendations to add :(")
            return 0
        self.info_logger(f"Found {len(highly_recommended_tracks)} highly recommended tracks!")

        num_tracks_to_add = min(len(highly_recommended_tracks), get_num_songs_to_add())
        highly_recommended_tracks = highly_recommended_tracks[:num_tracks_to_add]
        self.info_logger(f"Adding {num_tracks_to_add} tracks to the playlist..")
        self.music_api_client.add_tracks(playlist, highly_recommended_tracks)
        return num_tracks_to_add

    def _add_recommended_songs_that_match_strict_criteria(self, playlist, get_num_songs_to_add):
        song_attribute_ranges = self.music_util.get_strict_song_attribute_ranges(
            playlist, self.playlist_analyzer)
        self.info_logger(f"Got recommendation criteria:\n{song_attribute_ranges}")
        return self.add_recommended_songs(
            playlist, song_attribute_ranges, get_num_songs_to_add)

    def _add_recommended_songs_that_match_lenient_criteria(self, playlist, get_num_songs_to_add):
        song_attribute_ranges = self.music_util.get_lenient_song_attribute_ranges(playlist)
        self.info_logger(f"Got recommendation criteria:\n{song_attribute_ranges}")
        return self.add_recommended_songs(
            playlist, song_attribute_ranges, get_num_songs_to_add)

    def _get_tracks_from_my_saved_albums_with_same_genres(self, playlist, get_num_tracks_per_album, get_num_albums_to_fetch):
        """Skips albums that are already present in the playlist."""
        genres = self.music_util.get_common_genres_in_playlist(playlist)
        if len(genres) == 0:
            self.info_logger("There are no genres that all tracks in your playlist have in common :(")
            return []
        self.info_logger(f"The genres that all tracks in your playlist have in common are {', '.join(genres)}")

        matching_albums_in_your_library = self._get_my_albums_with_same_genres(genres, get_num_albums_to_fetch)
        self.info_logger(f"Found {len(matching_albums_in_your_library)} albums in your library that exactly match genres: {', '.join(genres)}")
        if len(matching_albums_in_your_library) == 0:
            return []

        return self._get_most_popular_tracks_if_albums_not_already_in_playlist(
            playlist, matching_albums_in_your_library, get_num_tracks_per_album)

    def _get_tracks_from_my_saved_albums_with_similar_genres(self, playlist, get_num_tracks_per_album, get_num_albums_to_fetch):
        "Less strict version of _get_tracks_from_my_saved_albums_with_same_genres"
        genres = self.music_util.get_highly_common_genres(playlist)
        matching_albums_in_your_library = self._get_my_albums_with_superset_genres(genres, get_num_albums_to_fetch)
        self.info_logger(f"Found {len(matching_albums_in_your_library)} albums in your library that contain genres: {', '.join(genres)}")
        if len(matching_albums_in_your_library) == 0:
            return []
        return self._get_most_popular_tracks_if_albums_not_already_in_playlist(
            playlist, matching_albums_in_your_library, get_num_tracks_per_album)

    def _get_most_popular_tracks_if_albums_not_already_in_playlist(self, playlist, matching_albums_in_your_library, get_num_tracks_per_album):
        tracks, num_tracks_per_album = [], get_num_tracks_per_album()
        for album in matching_albums_in_your_library:
            if playlist.has_any_tracks_from_album(album):
                self.info_logger(f"Oh! Skipping album '{album.name}' because it's already in the playlist.")
            else:
                most_popular_tracks = self.music_util.get_most_popular_tracks(
                    album, num_tracks_per_album)
                tracks.extend(most_popular_tracks)
        return tracks

    def _get_my_albums_with_same_genres(self, genres, get_num_albums_to_fetch):
        genre_matching_criteria = lambda playlist_genres, candidate_genres: set(playlist_genres) == set(candidate_genres)
        return self._get_my_matching_albums(genres, get_num_albums_to_fetch, genre_matching_criteria)

    def _get_my_albums_with_superset_genres(self, genres, get_num_albums_to_fetch):
        genre_matching_criteria = lambda playlist_genres, candidate_genres: set(playlist_genres) <= set(candidate_genres)
        return self._get_my_matching_albums(genres, get_num_albums_to_fetch, genre_matching_criteria)

    def _get_my_matching_albums(self, genres, get_num_albums_to_fetch, genre_matching_criteria):
        album_groups = self.my_music_lib.get_my_albums_grouped_by_genre(
            get_num_albums_to_fetch(), len(genres))
        for group in album_groups:
            if genre_matching_criteria(genres, group['genres']):
                self.info_logger(f"Good news! I found {len(group['albums'])} album(s) matching your playlist's genres:")
                self.info_logger(self.music_util.get_albums_as_readable_list(group['albums']))
                return group['albums']
        self.info_logger("Sorry, I couldn't find any albums matching your playlist's genres :(")
        return []