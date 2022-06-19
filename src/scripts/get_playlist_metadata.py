# allows me to run:
# $ python scripts/playlist_updater_example.py
import sys

sys.path.extend(['.', '../'])

from packages.music_management.music_util import MusicUtil
from packages.music_management.my_music_lib import MyMusicLib
from packages.music_api_clients.spotify import Spotify

def get_playlist_metadata(my_music_lib, playlist_name):
    playlist = my_music_lib.get_playlist_by_name(playlist_name)
    # from this, discovered https://github.com/okjuan/music-lib-bot/issues/13
    return (playlist, playlist.id, playlist.name, playlist.get_num_tracks())

def main():
    spotify = Spotify()
    music_util = MusicUtil(spotify, print)
    my_music_lib = MyMusicLib(spotify, music_util, print)
    print(get_playlist_metadata(my_music_lib, "tapestries"))

if __name__ == "__main__":
    main()