# allows me to run:
# $ python scripts/dump_playlist_genres.py
import sys
sys.path.extend(['.', '../'])

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.lib.playlist_creator import PlaylistCreator
from app.lib.playlist_stats import PlaylistStats
from app.lib.spotify_client_wrapper import SpotifyClientWrapper


def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)
    playlist_stats = PlaylistStats(my_music_lib, music_util, print)
    playlist_creator = PlaylistCreator(
        spotify_client_wrapper, my_music_lib, music_util, print)
    playlist = playlist_stats.get_playlist_with_track_audio_features(
        "buzz off mate - test copy")
    audio_features_min, audio_features_max = playlist_stats.get_audio_feature_representative_range(
        playlist)
    playlist_creator.add_recommended_songs_in_audio_feature_ranges(
        playlist, audio_features_min, audio_features_max, lambda: 10)


if __name__ == "__main__":
    main()