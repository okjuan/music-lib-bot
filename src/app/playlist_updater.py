from random import randint


DEFAULT_NUM_TRACKS_PER_ALBUM = 3
MIN_NUM_TRACKS_PER_ALBUM = 1
MAX_NUM_TRACKS_PER_ALBUM = 10
DEFAULT_NUM_ALBUMS_TO_FETCH = 50


class PlaylistUpdater:
    def __init__(self, music_lib_bot_helper, my_music_lib, music_util, ui):
        self.playlist = music_lib_bot_helper.get_playlist_name_from_user()
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.ui = ui
        self.playlist_genres = None

    def get_num_tracks_per_album(self):
        return self.ui.get_int_from_range(
            f"# of tracks per album to add to playlist? default is {DEFAULT_NUM_TRACKS_PER_ALBUM}",
            DEFAULT_NUM_TRACKS_PER_ALBUM,
            MIN_NUM_TRACKS_PER_ALBUM,
            MAX_NUM_TRACKS_PER_ALBUM
        )

    def get_num_albums_to_fetch(self):
        return self.ui.get_int(
            f"# of albums to fetch from your library? default is {DEFAULT_NUM_ALBUMS_TO_FETCH}",
            DEFAULT_NUM_ALBUMS_TO_FETCH
        )

    def should_continue(self):
        return self.ui.get_yes_or_no("Make more changes? y or no - default is 'n'", False)

    def run(self):
        while True:
            num_tracks_per_album = self.get_num_tracks_per_album()
            num_albums_to_fetch = self.get_num_albums_to_fetch()
            self.add_tracks_from_my_saved_albums_with_similar_genres(
                num_tracks_per_album, num_albums_to_fetch)
            if not self.should_continue():
                break
        self.ui.tell_user(f"Thanks for using Playlist Updater, catch ya next time.")

    def add_tracks_from_my_saved_albums_with_same_genres(self, num_tracks_per_album, num_albums_to_fetch):
        track_uris = self._get_tracks_from_my_saved_albums_with_same_genres(
            num_tracks_per_album, num_albums_to_fetch)

        if len(track_uris) == 0:
            print(f"Couldn't find any new tracks in your library with the same exact genres as your playlist '{self.playlist.name}'")
            print("Consider calling 'add_tracks_from_my_saved_albums_with_similar_genres' instead, which is less strict about genre matching")
            return

        print(f"Found {len(track_uris)} tracks with exact same genres as those already in your playlist..")
        self.add_tracks_in_random_positions(track_uris)

    def add_tracks_from_my_saved_albums_with_similar_genres(self, num_tracks_per_album, num_albums_to_fetch):
        "Less strict version of add_tracks_from_my_saved_albums_with_same_genres"
        track_uris = self._get_tracks_from_my_saved_albums_with_similar_genres(
            num_tracks_per_album, num_albums_to_fetch)

        if len(track_uris) == 0:
            print(f"Couldn't find any new tracks in your library with similar genres as those your playlist '{self.playlist.name}'")
            return

        print(f"Found {len(track_uris)} tracks with similar genres to those already in your playlist..")
        self.add_tracks_in_random_positions(track_uris)

    def add_tracks_in_random_positions(self, track_uris):
        if len(track_uris) == 0:
            print("Oops, no tracks given, so I can't add them to your playlist.")
        print(f"Adding {len(track_uris)} randomly throughout your playlist: '{self.playlist.name}'")
        for track in track_uris:
            random_position = randint(1, len(self.playlist.tracks)) if len(self.playlist.tracks) > 0 else 1
            self.my_music_lib.add_track_to_playlist_at_position(
                self.playlist.id, track, random_position)

    def shuffle(self):
        pass

    def remove_all_tracks_and_add_them_back_in(self):
        """Spotify weights their shuffle play feature based on how recently a song was added. This would reweight all songs evenly"""
        pass

    def _get_tracks_from_my_saved_albums_with_same_genres(self, num_tracks_per_album, num_albums_to_fetch):
        """Skips albums that are already present in the playlist."""
        genres = self._get_genres_in_common_in_playlist()
        if len(genres) == 0:
            print("There are no genres that all tracks in your playlist have in common :(")
            return []
        print(f"The genres that all tracks in your playlist have in common are {', '.join(genres)}")

        matching_albums_in_your_library = self._get_my_albums_with_same_genres(genres, num_albums_to_fetch)
        print(f"Found {len(matching_albums_in_your_library)} albums in your library that exactly match genres: {', '.join(genres)}")

        return self._get_most_popular_tracks_if_albums_not_already_in_playlist(
            matching_albums_in_your_library, num_tracks_per_album)

    def _get_tracks_from_my_saved_albums_with_similar_genres(self, num_tracks_per_album, num_albums_to_fetch):
        "Less strict version of _get_tracks_from_my_saved_albums_with_same_genres"
        genres = self._get_most_common_genres()
        if len(genres) == 0:
            print("Couldn't find any genres :(")
            return []
        print(f"Your playlist's most common genres are: {', '.join(genres)}")

        matching_albums_in_your_library = self._get_my_albums_with_superset_genres(genres, num_albums_to_fetch)
        print(f"Found {len(matching_albums_in_your_library)} albums in your library that contain genres: {', '.join(genres)}")

        return self._get_most_popular_tracks_if_albums_not_already_in_playlist(
            matching_albums_in_your_library, num_tracks_per_album)

    def _get_most_popular_tracks_if_albums_not_already_in_playlist(self, matching_albums_in_your_library, num_tracks_per_album):
        ids_of_albums_in_playlist, tracks = self.music_util.get_album_ids(self.playlist.tracks), []
        for album in matching_albums_in_your_library:
            if album.id in ids_of_albums_in_playlist:
                print(f"Oh! Skipping album '{album.name}' because it's already in the playlist.")
            else:
                most_popular_tracks = self.music_util.get_most_popular_tracks(
                    album, num_tracks_per_album)
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

    def _get_my_albums_with_same_genres(self, genres, num_albums_to_fetch):
        genre_matching_criteria = lambda playlist_genres, candidate_genres: set(playlist_genres) == set(candidate_genres)
        return self._get_my_matching_albums(genres, num_albums_to_fetch, genre_matching_criteria)

    def _get_my_albums_with_superset_genres(self, genres, num_albums_to_fetch):
        genre_matching_criteria = lambda playlist_genres, candidate_genres: set(playlist_genres) <= set(candidate_genres)
        return self._get_my_matching_albums(genres, num_albums_to_fetch, genre_matching_criteria)

    def _get_my_matching_albums(self, genres, num_albums_to_fetch, genre_matching_criteria):
        album_groups = self.my_music_lib.get_my_albums_grouped_by_genre(
            num_albums_to_fetch, len(genres))
        for group in album_groups:
            if genre_matching_criteria(genres, group['genres']):
                print(f"Good news! I found {len(group['albums'])} album(s) matching your playlist's genres:")
                print(self.music_util.get_albums_as_readable_list(group['albums']))
                return group['albums']
        print("Sorry, I couldn't find any albums matching your playlist's genres :(")
        return []