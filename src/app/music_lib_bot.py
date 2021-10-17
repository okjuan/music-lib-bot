# allows me to run:
# $ python scripts/music_lib_bot.py
import sys

sys.path.extend(['.', '../'])

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.lib.playlist_updater import PlaylistUpdater
from app.lib.spotify_client_wrapper import SpotifyClientWrapper
from app.lib.ui import ConsoleUI


DEFAULT_NUM_TRACKS_PER_ALBUM = 3
MIN_NUM_TRACKS_PER_ALBUM = 1
MAX_NUM_TRACKS_PER_ALBUM = 10
DEFAULT_NUM_ALBUMS_TO_FETCH = 50


class MusicLibBot:
    def __init__(self, my_music_lib, music_util, ui):
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.ui = ui

    def get_playlist(self):
        playlist = None
        while playlist is None:
            playlist_name = self.ui.get_string("What's the name of your playlist?")
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

    def should_continue(self):
        return self.ui.get_yes_or_no("Make more changes? y or no - default is 'n'", False)

    def run_playlist_updater(self):
        while True:
            playlist = self.get_playlist()
            playlist_updater = PlaylistUpdater(
                playlist, self.my_music_lib, self.music_util)
            num_tracks_per_album = self.get_num_tracks_per_album()
            num_albums_to_fetch = self.get_num_albums_to_fetch()
            playlist_updater.add_tracks_from_my_saved_albums_with_similar_genres(
                num_tracks_per_album, num_albums_to_fetch)
            if not self.should_continue():
                break
        self.ui.tell_user("See ya next time!")

def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)
    ui = ConsoleUI()
    MusicLibBot(my_music_lib, music_util, ui).run_playlist_updater()


if __name__ == "__main__":
    main()