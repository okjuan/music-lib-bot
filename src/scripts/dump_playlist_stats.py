# allows me to run:
# $ python scripts/dump_playlist_genres.py
import sys
sys.path.extend(['.', '../'])

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.lib.playlist_stats import PlaylistStats
from app.lib.spotify_client_wrapper import SpotifyClientWrapper


def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)
    playlist_stats = PlaylistStats(my_music_lib, music_util, print)
    playlist = playlist_stats.get_playlist_with_track_audio_features(
        "buzz off mate")
    for track in playlist.tracks:
        artist_names = [artist.name for artist in track.artists]
        print(f"'{track.name}' by {','.join(artist_names)}")
        print("\t", "danceability", track.audio_features.danceability)
        print("\t", "energy", track.audio_features.energy)
        print("\t", "key", track.audio_features.key)
        print("\t", "loudness", track.audio_features.loudness)
        print("\t", "mode", track.audio_features.mode)
        print("\t", "speechiness", track.audio_features.speechiness)
        print("\t", "acousticness", track.audio_features.acousticness)
        print("\t", "instrumentalness", track.audio_features.instrumentalness)
        print("\t", "liveness", track.audio_features.liveness)
        print("\t", "valence", track.audio_features.valence)
        print("\t", "tempo", track.audio_features.tempo)
        print("\t", "duration_ms", track.audio_features.duration_ms)
        print("\t", "time_signature", track.audio_features.time_signature)


if __name__ == "__main__":
    main()