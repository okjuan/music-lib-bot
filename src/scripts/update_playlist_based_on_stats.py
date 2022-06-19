# allows me to run:
# $ python scripts/dump_playlist_genres.py
import sys
sys.path.extend(['.', '../'])

from packages.music_management.music_util import MusicUtil
from packages.music_management.my_music_lib import MyMusicLib
from packages.music_management.playlist_updater import PlaylistUpdater
from packages.music_management.playlist_stats import PlaylistStats
from packages.music_api_clients.spotify_client_wrapper import SpotifyClientWrapper


def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper, print)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util, print)
    playlist_stats = PlaylistStats(my_music_lib, music_util, print)

    target_playlist = "kremwerk"
    print(f"Getting playlist '{target_playlist}' along with audio feature data")
    playlist = my_music_lib.get_playlist_by_name(target_playlist)
    music_util.populate_track_audio_features(playlist)

    if playlist is None:
        print(f"Couldn't find playlist '{target_playlist}'")
        return
    print(f"Got it!")

    playlist_updater = PlaylistUpdater(
        playlist,
        my_music_lib,
        music_util,
        spotify_client_wrapper,
        print,
        playlist_stats,
    )

    playlist_updater.add_recommended_songs_with_similar_attributes(
        lambda: 10)


if __name__ == "__main__":
    main()