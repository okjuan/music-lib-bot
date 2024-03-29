# allows me to run:
# $ python scripts/dump_playlist_genres.py
import sys
sys.path.extend(['.', '../'])

from packages.music_management.music_util import MusicUtil
from packages.music_management.my_music_lib import MyMusicLib
from packages.music_api_clients.spotify import Spotify


def main():
    spotify = Spotify()
    music_util = MusicUtil(spotify, print)
    my_music_lib = MyMusicLib(spotify, music_util, print)

    playlist_names = [
        "americana 4 PlaylistUpdater Test Playlist",
        #"bag of revels 4 PlaylistUpdater Test Playlist",
        #"art rock 4 PlaylistUpdater Test Playlist",
        #"between stations 4 PlaylistUpdater Test Playlist",
        #"buzz off 4 PlaylistUpdater",
        #"it's been easy 4 PlaylistUpdater Test Playlist",
        #"prize of Snell 4 PlaylistUpdater Test Playlist",
        #"velour 4 PlaylistUpdater"
    ]
    for playlist_name in playlist_names:
        playlist = my_music_lib.get_playlist_by_name(playlist_name)
        if playlist is None:
            print(f"Couldn't find your playlist '{playlist_name}'")
            continue

        genres_in_common = music_util.get_common_genres_in_playlist(playlist)
        genre_breakdown = music_util.get_genres_by_frequency(playlist)
        # ref: https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
        sorted_genre_breakdown = {
            k: v
            for k, v in sorted(genre_breakdown.items(), key=lambda item: item[1], reverse=True)
        }
        print(f"Playlist '{playlist_name}' has these genres in common: {genres_in_common}.")
        print(f"Num artists in playlist: {len(music_util.get_artists(playlist))}")
        print("...with this genre breakdown:")
        for genre, count in sorted_genre_breakdown.items():
            print(f"{count}\t{genre}")
        print()

def _print_in_order():
    pass

if __name__ == "__main__":
    main()