# allows me to run:
# $ python scripts/music_lib_bot.py
import sys

sys.path.extend(['.', '../'])

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.lib.playlist_updater import PlaylistUpdater
from app.lib.spotify_client_wrapper import SpotifyClientWrapper


class MusicLibBot:
    def __init__(self, my_music_lib, music_util):
        self.my_music_lib = my_music_lib
        self.music_util = music_util

    # TODO: implement
    def get_playlist(self):
        return self.my_music_lib.get_playlist_by_name("Test music_lib_bot.run_playlist_updater")

    # TODO: implement
    def get_num_tracks_per_album(self):
        return 3

    # TODO: implement
    def get_num_albums_to_fetch(self):
        return 100

    def run_playlist_updater(self):
        # TODO while True:
        for i in range(1):
            playlist = self.get_playlist()
            playlist_updater = PlaylistUpdater(
                playlist, self.my_music_lib, self.music_util)
            num_tracks_per_album = self.get_num_tracks_per_album()
            num_albums_to_fetch = self.get_num_albums_to_fetch()
            playlist_updater.add_tracks_from_my_saved_albums_with_similar_genres(
                num_tracks_per_album, num_albums_to_fetch)


def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)
    MusicLibBot(my_music_lib, music_util).run_playlist_updater()


if __name__ == "__main__":
    main()