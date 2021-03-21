from music_lib_api import MusicLibApi


SELECTION_QUIT_APP = "Quit"
QUIT_KEY = "q"
DEFAULT_ALBUMS_TO_FETCH = 50
DEFAULT_LOOK_AT_ENTIRE_LIBRARY = False
DEFAULT_NUM_TRACKS_PER_ALBUM = 3
DEFAULT_MIN_ALBUMS_PER_PLAYLIST = 4
DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST = 4
DEFAULT_MIN_GENRES_PER_PLAYLIST = 4

class PlaylistPicker:
    def __init__(self):
        self.music_lib_api = MusicLibApi()

    def get_preference_int(self, prompt):
        return self.parse_int(self.prompt_user(prompt))

    def get_preference_yes_or_no(self, prompt):
        return self.parse_yes_or_no(self.prompt_user(prompt))

    def prompt_user(self, msg):
        return input(f"\n> {msg}\n")

    def if_none(self, val, default):
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

    def get_min_albums_per_playlist(self):
        return self.if_none(
            self.get_preference_int(f"Minimum # of albums per playlist? default is {DEFAULT_MIN_ALBUMS_PER_PLAYLIST}"),
            DEFAULT_MIN_ALBUMS_PER_PLAYLIST
        )

    def get_min_artists_per_playlist(self):
        return self.if_none(
            self.get_preference_int(f"Minimum # of artists per playlist? default is {DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST}"),
            DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST
        )

    def set_up_options(self, albums_by_genre):
        min_albums_per_playlist = self.get_min_albums_per_playlist()
        min_artists_per_playlist = self.get_min_artists_per_playlist()
        criteria = lambda albums: len(albums) >= min_albums_per_playlist and self.get_num_diff_artists(albums) >= min_artists_per_playlist
        return [
            dict(description=genre_group, albums=albums)
            for genre_group, albums in albums_by_genre.items()
            if criteria(albums)
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

    def get_num_tracks_per_album(self):
        return self.if_none(
            self.get_preference_int(f"Minimum # of tracks per album per playlist? default is {DEFAULT_NUM_TRACKS_PER_ALBUM}"),
            DEFAULT_NUM_TRACKS_PER_ALBUM
        )

    def create_playlist_from_albums(self, album_group):
        print(f"Creating '{album_group['description']}' playlist from {len(album_group['albums'])} albums...")
        tracks = self.music_lib_api.get_tracks_from_each(album_group["albums"], self.get_num_tracks_per_album())
        self.music_lib_api.create_playlist(
            album_group["description"],
            tracks,
            description="created by music.lib.bot"
        )
        print(f"Playlist created!")

    def launch_ui(self, options):
        while True:
            selection = self.get_selection(options)
            if selection is SELECTION_QUIT_APP:
                print("Quitting...")
                break

            self.create_playlist_from_albums(options[selection])
            if not self.user_wants_to_create_another_playlist():
                break

    def get_num_diff_artists(self, albums):
        return len({
            artist['id']
            for album in albums
            for artist in album["artists"]
        })

    def get_min_genres_per_group(self):
        return self.if_none(
            self.get_preference_int(f"Minimum # of genres per playlist? default is {DEFAULT_MIN_GENRES_PER_PLAYLIST}"),
            DEFAULT_MIN_GENRES_PER_PLAYLIST
        )

    def look_at_entire_library(self):
        return self.if_none(
            self.get_preference_yes_or_no(f"Should I look at your entire library? y or n - default is {'y' if DEFAULT_LOOK_AT_ENTIRE_LIBRARY else 'n'}"),
            DEFAULT_LOOK_AT_ENTIRE_LIBRARY
        )

    def get_num_albums_to_fetch(self):
        return self.if_none(
            self.get_preference_int(f"# of albums to fetch from your library? default is {DEFAULT_ALBUMS_TO_FETCH}"),
            DEFAULT_ALBUMS_TO_FETCH
        )

    def user_wants_to_create_another_playlist(self):
        return self.if_none(
            self.get_preference_yes_or_no(f"Create another playlist? y or n - default is 'y'"),
            True
        )

    def get_albums_by_genre(self):
        min_genres_per_group = self.get_min_genres_per_group()
        if self.look_at_entire_library():
            albums_by_genre = self.music_lib_api.get_all_my_albums_grouped_by_genre(
                min_genres_per_group)
        else:
            albums_by_genre = self.music_lib_api.get_my_albums_grouped_by_genre(
                self.get_num_albums_to_fetch(), min_genres_per_group)
        return albums_by_genre

    def run(self):
        options = self.set_up_options(self.get_albums_by_genre())
        if len(options) == 0:
            print("Didn't find any options to select from!")
            return
        self.launch_ui(options)
        print(f"Happy listening!")


if __name__ == "__main__":
    PlaylistPicker().run()