class PlaylistUpdater:
    def __init__(self, playlist, my_music_lib, music_util, spotify_client, info_logger):
        self.playlist = playlist
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.spotify_client = spotify_client
        self.info_logger = info_logger
        self.playlist_genres = None

    def add_tracks_from_my_saved_albums_with_same_genres(self, get_num_tracks_per_album, get_num_albums_to_fetch):
        track_uris = self._get_tracks_from_my_saved_albums_with_same_genres(
            get_num_tracks_per_album, get_num_albums_to_fetch)

        if len(track_uris) == 0:
            self.info_logger(f"Couldn't find any new tracks in your library with the same exact genres as your playlist '{self.playlist.name}'")
            self.info_logger("Consider calling 'add_tracks_from_my_saved_albums_with_similar_genres' instead, which is less strict about genre matching")
            return

        self.info_logger(f"Found {len(track_uris)} tracks with exact same genres as those already in your playlist..")
        self.my_music_lib.add_tracks_in_random_positions(track_uris)

    def add_tracks_from_my_saved_albums_with_similar_genres(self, get_num_tracks_per_album, get_num_albums_to_fetch):
        "Less strict version of add_tracks_from_my_saved_albums_with_same_genres"
        track_uris = self._get_tracks_from_my_saved_albums_with_similar_genres(
            get_num_tracks_per_album, get_num_albums_to_fetch)

        if len(track_uris) == 0:
            self.info_logger(f"Couldn't find any new tracks in your library with similar genres as those your playlist '{self.playlist.name}'")
            return

        self.info_logger(f"Found {len(track_uris)} tracks with similar genres to those already in your playlist..")
        self.my_music_lib.add_tracks_in_random_positions(track_uris)

    def add_recommended_songs(self, playlist, recommendation_criteria, get_num_songs_to_add):
        """
        Params:
            playlist (Playlist).
            recommendation_criteria (RecommendationCriteria).
            get_num_songs_to_add (lambda): takes 0 params, returns int.
        """
        self.info_logger("Getting recommendations..")
        recommended_tracks = self.music_util.get_recommendations_based_on_tracks(
            [track.id for track in playlist.tracks],
            get_num_songs_to_add(),
            recommendation_criteria,
        )
        self.info_logger(f"Got {len(recommended_tracks)} recommended tracks")
        self.info_logger("Adding tracks to the playlist..")
        self.spotify_client.add_tracks(
            playlist.id, [track.id for track in recommended_tracks])

    def _get_tracks_from_my_saved_albums_with_same_genres(self, get_num_tracks_per_album, get_num_albums_to_fetch):
        """Skips albums that are already present in the playlist."""
        genres = self._get_genres_in_common_in_playlist()
        if len(genres) == 0:
            self.info_logger("There are no genres that all tracks in your playlist have in common :(")
            return []
        self.info_logger(f"The genres that all tracks in your playlist have in common are {', '.join(genres)}")

        matching_albums_in_your_library = self._get_my_albums_with_same_genres(genres, get_num_albums_to_fetch)
        self.info_logger(f"Found {len(matching_albums_in_your_library)} albums in your library that exactly match genres: {', '.join(genres)}")

        return self._get_most_popular_tracks_if_albums_not_already_in_playlist(
            matching_albums_in_your_library, get_num_tracks_per_album)

    def _get_tracks_from_my_saved_albums_with_similar_genres(self, get_num_tracks_per_album, get_num_albums_to_fetch):
        "Less strict version of _get_tracks_from_my_saved_albums_with_same_genres"
        genres = self._get_most_common_genres()
        if len(genres) == 0:
            self.info_logger("Couldn't find any genres :(")
            return []
        self.info_logger(f"Your playlist's most common genres are: {', '.join(genres)}")

        matching_albums_in_your_library = self._get_my_albums_with_superset_genres(genres, get_num_albums_to_fetch)
        self.info_logger(f"Found {len(matching_albums_in_your_library)} albums in your library that contain genres: {', '.join(genres)}")

        return self._get_most_popular_tracks_if_albums_not_already_in_playlist(
            matching_albums_in_your_library, get_num_tracks_per_album)

    def _get_most_popular_tracks_if_albums_not_already_in_playlist(self, matching_albums_in_your_library, get_num_tracks_per_album):
        ids_of_albums_in_playlist, tracks = self.music_util.get_album_ids(self.playlist.tracks), []
        for album in matching_albums_in_your_library:
            if album.id in ids_of_albums_in_playlist:
                self.info_logger(f"Oh! Skipping album '{album.name}' because it's already in the playlist.")
            else:
                most_popular_tracks = self.music_util.get_most_popular_tracks(
                    album, get_num_tracks_per_album())
                tracks.extend([track.uri for track in most_popular_tracks])
        return tracks

    def _get_genres_in_common_in_playlist(self):
        if self.playlist_genres is None:
            self.playlist_genres = self.music_util.get_common_genres_in_playlist(self.playlist.id)
        return self.playlist_genres

    def _get_most_common_genres(self):
        "Returns top 10% most common genres. If 10% < 1 then return most common genre."
        if self.playlist_genres is not None:
            return self.playlist_genres

        target_genres = self.music_util.get_genres_by_frequency(self.playlist.id)
        target_genres_list = [(genre, count) for genre, count in target_genres.items()]
        target_genres_list.sort(key=lambda pair: pair[1], reverse=True)
        top_10_percent = max(int(len(target_genres_list)/10), 1)
        self.playlist_genres = [genre for genre, _ in target_genres_list[:top_10_percent]]
        return self.playlist_genres

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