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
from app.playlist_picker import PlaylistPicker


class MusicLibBot:
    def __init__(self, my_music_lib, music_util, ui):
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.ui = ui

    def run_playlist_updater(self):
        PlaylistUpdater(
            MusicLibBotHelper(self.my_music_lib, self.ui),
            self.my_music_lib,
            self.music_util,
            self.ui
        ).run()

    def run_playlist_creator(self):
        PlaylistPicker(
            MusicLibBotHelper(self.my_music_lib, self.ui),
            self.my_music_lib,
            self.music_util,
            self.ui
        ).run()

    def run(self):
        apps = {
            "a": self.run_playlist_updater,
            "b": self.run_playlist_creator,
        }
        while True:
            selection = self.ui.get_string_from_options(
                "What app do you want to use? Pick an option:\n\t'a' - Playlist Updater\n\t'b' - Playlist Creator\n\t'q' - quit",
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
    MusicLibBot(my_music_lib, music_util, ui).run()


if __name__ == "__main__":
    main()