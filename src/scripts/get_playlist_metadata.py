# allows me to run:
# $ python scripts/playlist_updater_example.py
import sys

sys.path.extend(['.', '../'])

from packages.music_management.music_util import MusicUtil
from packages.music_management.my_music_lib import MyMusicLib
from packages.spotify.spotify_client_wrapper import SpotifyClientWrapper

def get_playlist_metadata(my_music_lib, playlist_name):
    playlist = my_music_lib.get_playlist_by_name(playlist_name)
    # from this, discovered https://github.com/okjuan/music-lib-bot/issues/13
    return (playlist, playlist.id, playlist.name, playlist.get_num_tracks())

def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper, print)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util, print)
    print(get_playlist_metadata(my_music_lib, "tapestries"))

if __name__ == "__main__":
    main()