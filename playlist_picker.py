from music_lib_api import MusicLibApi


SELECTION_QUIT_APP = "Quit"
QUIT_KEY = "q"
MIN_GROUP_SIZE = 1
MUSIC_LIB_API = None

class PlaylistPicker:
    def __init__(self):
        self.music_lib_api = MusicLibApi()

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

        try:
            selection_int = int(selection.strip())
        except ValueError:
            return None

        if selection_int >= min_option and selection_int <= max_option:
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
            self.music_lib_api.get_tracks_from_each(album_group["albums"]),
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
        albums_by_genre = self.music_lib_api.get_my_albums_grouped_by_genre()

        options = self.set_up_options(albums_by_genre)
        if len(options) == 0:
            print("Didn't find any options to select from!")
            return

        self.launch_ui(options)
        print(f"Happy listening!")


if __name__ == "__main__":
    PlaylistPicker().run()