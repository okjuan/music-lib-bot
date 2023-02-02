# allows me to run:
# $ python scripts/dump_playlist_genres.py
import sys
sys.path.extend(['.', '../'])

from packages.music_management.my_music_lib import MyMusicLib
from packages.music_management.music_util import MusicUtil
from packages.music_management.playlist_updater import PlaylistUpdater
from packages.music_management.playlist_analyzer import PlaylistAnalyzer
from packages.music_api_clients.spotify import Spotify

NUM_TRACKS_PER_ALBUM = 3


def main():
    spotify = Spotify()
    music_util = MusicUtil(spotify, print)
    my_music_lib = MyMusicLib(spotify, music_util, print)
    playlist_analyzer = PlaylistAnalyzer(my_music_lib, music_util, print)

    seed_prefix = "seed: "
    seed_playlists = my_music_lib.search_my_playlists(seed_prefix)
    print(f"Found {len(seed_playlists)} matching playlists.")

    get_target_playlist_name = lambda seed_playlist: seed_playlist.name[len(seed_prefix):]
    updates = PlaylistUpdater(
        my_music_lib,
        music_util,
        spotify,
        print,
        playlist_analyzer
    ).create_or_update_all_targets_from_seeds(seed_playlists, 3, get_target_playlist_name)

    for update in updates:
        print(f"Added {update[1]} songs to playlist '{update[0].name}'.")


if __name__ == "__main__":
    main()