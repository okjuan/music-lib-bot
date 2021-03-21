from music_lib_api import MusicLibApi


SELECTION_QUIT_APP = "Quit"
QUIT_KEY = "q"
MIN_GROUP_SIZE = 1
MUSIC_LIB_API = None
DEFAULT_ALBUMS_TO_FETCH = 50
DEFAULT_LOOK_AT_ENTIRE_LIBRARY = False
DEFAULT_NUM_DAYS_TO_LOOK_BACK = 15
DEFAULT_MIN_GENRES_PER_GROUP = 4
NUM_TRACKS_PER_ALBUM = 3

class PlaylistPicker:
    def set_up_user_preferences(self):
        min_genres_per_group = self.get_preference_int(
            "What is the minimum number of genres you want per playlist?",
            DEFAULT_MIN_GENRES_PER_GROUP
        )

        num_tracks_per_album = self.get_preference_int(
            "What is the minimum number of tracks you want per album per playlist?",
            NUM_TRACKS_PER_ALBUM
        )

        look_at_entire_library = self.get_preference_yes_or_no(
            "Should I look at your entire library? (y or n)",
            DEFAULT_LOOK_AT_ENTIRE_LIBRARY
        )

        if look_at_entire_library:
            self.music_lib_api = MusicLibApi(
                look_at_entire_library=look_at_entire_library,
                min_genres_per_group=min_genres_per_group,
            )
        else:
            albums_to_fetch = self.get_preference_int(
                "How many albums should I fetch from your library?",
                DEFAULT_ALBUMS_TO_FETCH
            )
            num_days_to_look_back = self.get_preference_int(
                "How many days should I look back for recently saved albums?",
                DEFAULT_NUM_DAYS_TO_LOOK_BACK
            )
            self.music_lib_api = MusicLibApi(
                albums_to_fetch=albums_to_fetch,
                look_at_entire_library=look_at_entire_library,
                num_days_to_look_back=num_days_to_look_back,
                min_genres_per_group=min_genres_per_group,
            )

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
            if len(albums) >= MIN_GROUP_SIZE
        ]

    def print_playlist_options(self, options):
        print("\nHere are your options for creating a playlist from albums in your library:")
        for idx, album_groups in enumerate(options):
            print(f"#{idx}\n\tDescription: {album_groups['description']}\n\tNumber of albums: {len(album_groups['albums'])}")
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
            "created by music.lib.bot",
            self.music_lib_api.get_tracks_from_each(album_group["albums"], NUM_TRACKS_PER_ALBUM),
            description=album_group["description"]
        )

    def launch_ui(self, options):
        while True:
            selection = self.get_selection(options)
            if selection is SELECTION_QUIT_APP:
                print("Quitting...")
                break
            self.create_playlist_from_albums(options[selection])

    def run(self):
        self.set_up_user_preferences()
        albums_by_genre = self.music_lib_api.get_my_albums_grouped_by_genre()

        options = self.set_up_options(albums_by_genre)
        if len(options) == 0:
            print("Didn't find any options to select from!")
            return

        self.launch_ui(options)
        print(f"Happy listening!")


if __name__ == "__main__":
    PlaylistPicker().run()