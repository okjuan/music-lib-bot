# allows me to run:
# $ python scripts/music_lib_bot.py
import sys

sys.path.extend(['.', '../'])

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.playlist_updater import PlaylistUpdater
from app.lib.spotify_client_wrapper import SpotifyClientWrapper
from app.lib.ui import ConsoleUI
from app.playlist_picker import PlaylistPicker


class MusicLibBot:
    def __init__(self, my_music_lib, music_util, ui):
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.ui = ui

    def _get_playlist(self):
        playlist = None
        while playlist is None:
            playlist_name = self.ui.get_string("What's the name of your playlist?")
            playlist = self.my_music_lib.get_playlist_by_name(playlist_name)
            if playlist is None:
                self.ui.tell_user(f"I couldn't find '{playlist_name}' in your playlists.")
        return playlist

    def run_playlist_updater(self):
        PlaylistUpdater(self._get_playlist(), self.my_music_lib, self.music_util, self.ui).run()

    def run_playlist_creator(self):
        PlaylistPicker(self.my_music_lib, self.music_util, self.ui).run()

    def run(self):
        apps = {
            "a": self.run_playlist_updater,
            "b": self.run_playlist_creator,
        }
        selection = self.ui.get_string_from_options(
            "What app do you want to use? Pick an option:\n\t'a' - Playlist Updater\n\t'b' - Playlist Creator",
            ["a", "b"]
        )
        apps[selection]()


def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)
    ui = ConsoleUI()
    MusicLibBot(my_music_lib, music_util, ui).run()


if __name__ == "__main__":
    main()