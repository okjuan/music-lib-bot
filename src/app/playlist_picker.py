# allows me to run:
# $ python app/playlist_picker.py
import sys
sys.path.extend(['.', '../'])

from random import shuffle

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.lib.spotify_client_wrapper import SpotifyClientWrapper
from app.lib.ui import ConsoleUI


QUIT = -1
DEFAULT_ALBUMS_TO_FETCH = 50
DEFAULT_LOOK_AT_ENTIRE_LIBRARY = False
DEFAULT_NUM_TRACKS_PER_ALBUM = 3
DEFAULT_MIN_ALBUMS_PER_PLAYLIST = 4
DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST = 4
DEFAULT_MIN_GENRES_PER_PLAYLIST = 4
MIN_PLAYLIST_SUGGESTIONS_TO_SHOW = 10

class PlaylistPicker:
    def __init__(self, my_music_lib, music_util, ui):
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.ui = ui

    def get_min_albums_per_playlist(self):
        return self.ui.get_int(
            f"Minimum # of albums per playlist? default is {DEFAULT_MIN_ALBUMS_PER_PLAYLIST}",
            DEFAULT_MIN_ALBUMS_PER_PLAYLIST
        )

    def get_min_artists_per_playlist(self):
        return self.ui.get_int(
            f"Minimum # of artists per playlist? default is {DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST}",
            DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST
        )

    def get_suggested_playlists(self, albums_by_genre):
        min_albums_per_playlist = self.get_min_albums_per_playlist()
        min_artists_per_playlist = self.get_min_artists_per_playlist()
        playlist_criteria = lambda albums: len(albums) >= min_albums_per_playlist and self.get_num_diff_artists(albums) >= min_artists_per_playlist
        return [
            dict(
                description=', '.join(album_group['genres']),
                albums=album_group['albums']
            )
            for album_group in albums_by_genre
            if playlist_criteria(album_group['albums'])
        ]

    def give_playlist_options(self, num_options, options):
        # TODO: remove/replace \n, \t chars, etc.
        self.ui.tell_user("\nHere are your options for creating a playlist from albums in your library.")
        self.ui.tell_user("The options are ordered by number of albums from most to least.")
        options.sort(
            key=lambda album_group: len(album_group['albums']),
            reverse=True
        )
        for idx, album_group in enumerate(options[:num_options]):
            artists = list({artist['name'] for album in album_group['albums'] for artist in album.artists})
            self.ui.tell_user(f"#{idx}\n\tDescription: {album_group['description']}\n\tNumber of albums: {len(album_group['albums'])}\n\tArtists: {', '.join(artists)}")

    def get_num_options_desired(self, options):
        if len(options) <= MIN_PLAYLIST_SUGGESTIONS_TO_SHOW:
            return len(options)

        min_option, max_option = 1, len(options)
        message = f"How many playlist options do you want to see?\n\t(Enter a number between {min_option} and {max_option})\n"
        return self.ui.get_int_from_range(
            message, min_option, max_option)

    def get_selection(self, suggested_playlists):
        num_options = self.get_num_options_desired(suggested_playlists)
        min_option, max_option = 0, len(suggested_playlists)-1
        message = f"Please select which playlist to create!\nEnter a number between {min_option} and {max_option} or enter {QUIT} to quit:"
        self.give_playlist_options(num_options, suggested_playlists)
        options = [QUIT, *self._get_indices_as_list(suggested_playlists)]
        return self.ui.get_from_options(message, options)

    def _get_indices_as_list(self, list_):
        return list(range(len(list_)))

    def get_num_tracks_per_album(self):
        return self.ui.get_int(
            f"How many tracks per album per playlist? default is {DEFAULT_NUM_TRACKS_PER_ALBUM}",
            DEFAULT_NUM_TRACKS_PER_ALBUM
        )

    def create_playlist_from_albums(self, album_group):
        tracks = self.music_util.get_most_popular_tracks_from_each(
            album_group["albums"], self.get_num_tracks_per_album())
        shuffle(tracks)

        self.ui.tell_user(f"Creating '{album_group['description']}' playlist from {len(album_group['albums'])} albums...")
        self.my_music_lib.create_playlist(
            album_group["description"],
            [track.uri for track in tracks],
            description="created by playlist_picker"
        )
        self.ui.tell_user(f"Playlist created!")

    def launch_interactive_playlist_creator(self, suggested_playlists):
        while True:
            selection = self.get_selection(suggested_playlists)
            if selection is QUIT:
                self.ui.tell_user("Quitting...")
                break

            self.create_playlist_from_albums(suggested_playlists[selection])
            if not self.user_wants_to_create_another_playlist():
                break

    def get_num_diff_artists(self, albums):
        return len({
            artist['id']
            for album in albums
            for artist in album.artists
        })

    def get_min_genres_per_group(self):
        return self.ui.get_int(
            f"Minimum # of genres per playlist? default is {DEFAULT_MIN_GENRES_PER_PLAYLIST}",
            DEFAULT_MIN_GENRES_PER_PLAYLIST
        )

    def look_at_entire_library(self):
        return self.ui.get_yes_or_no(
            f"Should I look at your entire library? y or n - default is {'y' if DEFAULT_LOOK_AT_ENTIRE_LIBRARY else 'n'}",
            DEFAULT_LOOK_AT_ENTIRE_LIBRARY
        )

    def get_num_albums_to_fetch(self):
        return self.ui.get_int(
            f"# of albums to fetch from your library? default is {DEFAULT_ALBUMS_TO_FETCH}",
            DEFAULT_ALBUMS_TO_FETCH
        )

    def user_wants_to_create_another_playlist(self):
        return self.ui.get_yes_or_no(
            f"Create another playlist? y or n - default is 'y'",
            True
        )

    def get_albums_by_genre(self):
        min_genres_per_group = self.get_min_genres_per_group()
        if self.look_at_entire_library():
            albums_by_genre = self.my_music_lib.get_all_my_albums_grouped_by_genre(
                min_genres_per_group)
        else:
            albums_by_genre = self.my_music_lib.get_my_albums_grouped_by_genre(
                self.get_num_albums_to_fetch(), min_genres_per_group)
        return albums_by_genre

    def run(self):
        albums_by_genre = self.get_albums_by_genre()
        suggested_playlists = self.get_suggested_playlists(albums_by_genre)
        if len(suggested_playlists) == 0:
            self.ui.tell_user("Couldn't find any suggested playlists!")
            return
        self.launch_interactive_playlist_creator(suggested_playlists)
        self.ui.tell_user(f"Happy listening!")


def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)
    ui = ConsoleUI()
    PlaylistPicker(my_music_lib, music_util, ui).run()


if __name__ == "__main__":
    main()