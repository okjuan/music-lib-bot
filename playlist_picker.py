from music_lib_api import MusicLibApi


SELECTION_QUIT_APP = "Quit"
QUIT_KEY = "q"
MUSIC_LIB_API = None
DEFAULT_ALBUMS_TO_FETCH = 50
DEFAULT_LOOK_AT_ENTIRE_LIBRARY = False
DEFAULT_NUM_TRACKS_PER_ALBUM = 3
DEFAULT_MIN_ALBUMS_PER_PLAYLIST = 1
DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST = 1
DEFAULT_MIN_GENRES_PER_GROUP = 4
MIN_ALBUMS_PER_PLAYLIST = DEFAULT_MIN_ALBUMS_PER_PLAYLIST
MIN_NUM_ARTISTS_PER_PLAYLIST = DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST
NUM_TRACKS_PER_ALBUM = DEFAULT_NUM_TRACKS_PER_ALBUM


class PlaylistPicker:
    def set_up_user_preferences(self):
        global MIN_ALBUMS_PER_PLAYLIST, MIN_NUM_ARTISTS_PER_PLAYLIST

        self.min_genres_per_group = self.get_preference_int(
            "Minimum # of genres per playlist?",
            DEFAULT_MIN_GENRES_PER_GROUP
        )

        MIN_ALBUMS_PER_PLAYLIST = self.get_preference_int(
            "Minimum # of albums per playlist?",
            DEFAULT_MIN_ALBUMS_PER_PLAYLIST
        )

        MIN_NUM_ARTISTS_PER_PLAYLIST = self.get_preference_int(
            "Minimum # of artists per playlist?",
            DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST
        )

        NUM_TRACKS_PER_ALBUM = self.get_preference_int(
            "Minimum # of tracks per album per playlist?",
            DEFAULT_NUM_TRACKS_PER_ALBUM
        )

        self.look_at_entire_library = self.get_preference_yes_or_no(
            "Should I look at your entire library? (y or n)",
            DEFAULT_LOOK_AT_ENTIRE_LIBRARY
        )

        if not self.look_at_entire_library:
            self.albums_to_fetch = self.get_preference_int(
                "How many albums should I fetch from your library?",
                DEFAULT_ALBUMS_TO_FETCH
            )

        self.music_lib_api = MusicLibApi()

    def get_preference_int(self, prompt, default):
        return self.unless_none(self.parse_int(input(prompt+"\n")), default)

    def get_preference_yes_or_no(self, prompt, default):
        return self.unless_none(self.parse_yes_or_no(input(prompt+"\n")), default)

    def unless_none(self, val, default):
        return default if val is None else val

    def parse_int(self, input_str):
        try:
            return int(input_str.strip())
        except ValueError:
            return None

    def parse_yes_or_no(self, input_str):
        answer = input_str.strip().lower()
        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            return None

    def set_up_options(self, albums_by_genre):
        return [
            dict(description=genre_group, albums=albums)
            for genre_group, albums in albums_by_genre.items()
            if len(albums) >= MIN_ALBUMS_PER_PLAYLIST and self.get_num_diff_artists(albums) >= MIN_NUM_ARTISTS_PER_PLAYLIST
        ]

    def print_playlist_options(self, options):
        print("\nHere are your options for creating a playlist from albums in your library:")
        for idx, album_groups in enumerate(options):
            artists = list({artist['name'] for album in album_groups['albums'] for artist in album['artists']})
            print(f"#{idx}\n\tDescription: {album_groups['description']}\n\tNumber of albums: {len(album_groups['albums'])}\n\tArtists: {', '.join(artists)}")
        print()

    def get_user_selection(self, min_option, max_option):
        selection = None
        while selection is None:
            selection = self.parse_selection(min_option, max_option)
        return selection

    def parse_selection(self, min_option, max_option):
        selection = input(
            f"Please select which playlist to create!\nEnter a number between {min_option} and {max_option} or enter '{QUIT_KEY}' to quit:\n")

        if selection.strip() == QUIT_KEY:
            return SELECTION_QUIT_APP

        selection_int = self.parse_int(selection)
        if selection_int is not None and selection_int >= min_option and selection_int <= max_option:
            return selection_int
        return None

    def get_selection(self, options):
        self.print_playlist_options(options)
        selection = self.get_user_selection(0, len(options)-1)
        return selection

    def create_playlist_from_albums(self, album_group):
        print(f"Creating '{album_group['description']}' playlist from {len(album_group['albums'])} albums...")
        self.music_lib_api.create_playlist(
            album_group["description"],
            self.music_lib_api.get_tracks_from_each(album_group["albums"], NUM_TRACKS_PER_ALBUM),
            description="created by music.lib.bot"
        )

    def launch_ui(self, options):
        while True:
            selection = self.get_selection(options)
            if selection is SELECTION_QUIT_APP:
                print("Quitting...")
                break
            self.create_playlist_from_albums(options[selection])

    def get_num_diff_artists(self, albums):
        return len({
            artist['id']
            for album in albums
            for artist in album["artists"]
        })

    def get_albums_by_genre(self):
        if self.look_at_entire_library:
            albums_by_genre = self.music_lib_api.get_all_my_albums_grouped_by_genre(
                self.min_genres_per_group)
        else:
            albums_by_genre = self.music_lib_api.get_my_albums_grouped_by_genre(
                self.albums_to_fetch, self.min_genres_per_group)
        return albums_by_genre

    def run(self):
        self.set_up_user_preferences()
        options = self.set_up_options(self.get_albums_by_genre())
        if len(options) == 0:
            print("Didn't find any options to select from!")
            return

        self.launch_ui(options)
        print(f"Happy listening!")


if __name__ == "__main__":
    PlaylistPicker().run()