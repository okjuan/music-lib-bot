# allows me to run:
# $ python scripts/music_lib_bot.py
import sys

sys.path.extend(['.', '../'])

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.lib.music_lib_bot_helper import MusicLibBotHelper
from app.playlist_updater import PlaylistUpdater
from app.lib.spotify_client_wrapper import SpotifyClientWrapper
from app.lib.ui import ConsoleUI
from app.playlist_creator import PlaylistCreator

DEFAULT_NUM_TRACKS_PER_ALBUM = 3
MIN_NUM_TRACKS_PER_ALBUM = 1
MAX_NUM_TRACKS_PER_ALBUM = 10
DEFAULT_NUM_ALBUMS_TO_FETCH = 50


class MusicLibBot:
    def __init__(self, spotify_client, my_music_lib, music_util, ui):
        self.spotify_client = spotify_client
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.ui = ui

    def run_playlist_updater(self):
        while True:
            playlist = self.get_playlist_from_user()
            playlist_updater = PlaylistUpdater(
                playlist,
                self.my_music_lib,
                self.music_util,
            )
            playlist_updater.add_tracks_from_my_saved_albums_with_similar_genres__lazy(
                self.get_num_tracks_per_album, self.get_num_albums_to_fetch)

            if not self.user_wants_to_continue():
                break
        self.ui.tell_user(f"Thanks for using Playlist Updater, catch ya next time.")

    def user_wants_to_continue(self):
        return self.ui.get_yes_or_no("Make more changes? y or no - default is 'n'", False)

    def run_playlist_creator(self):
        PlaylistCreator(
            self.spotify_client,
            MusicLibBotHelper(self.my_music_lib, self.ui),
            self.my_music_lib,
            self.music_util,
            self.ui
        ).run()

    def get_playlist_from_user(self):
        playlist = None
        while playlist is None:
            playlist_name = self.ui.get_non_empty_string(
                "What's the name of your playlist?")
            playlist = self.my_music_lib.get_playlist_by_name(playlist_name)
            if playlist is None:
                self.ui.tell_user(f"I couldn't find '{playlist_name}' in your playlists.")
        return playlist

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

    def run(self):
        apps = {
            "a": self.run_playlist_creator,
            "b": self.run_playlist_updater,
        }
        while True:
            selection = self.ui.get_string_from_options(
                "What app do you want to use? Pick an option:\n\t'a' - Playlist Creator\n\t'b' - Add Tracks to My Playlist from My Saved Albums with Similar Genres\n\t'q' - quit",
                ["a", "b", "q"]
            )
            if selection == 'q':
                self.ui.tell_user("Happy listening!")
                break
            apps[selection]()


def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)
    ui = ConsoleUI()
    MusicLibBot(spotify_client_wrapper, my_music_lib, music_util, ui).run()


if __name__ == "__main__":
    main()