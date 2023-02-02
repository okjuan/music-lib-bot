# allows me to run:
# $ python scripts/dump_playlist_genres.py
import sys
sys.path.extend(['.', '../'])

from packages.music_management.my_music_lib import MyMusicLib
from packages.music_management.music_util import MusicUtil
from packages.music_management.playlist_updater import PlaylistUpdater
from packages.music_management.playlist_stats import PlaylistStats
from packages.music_api_clients.spotify import Spotify

NUM_TRACKS_PER_ALBUM = 3


def main():
    spotify = Spotify()
    music_util = MusicUtil(spotify, print)
    my_music_lib = MyMusicLib(spotify, music_util, print)
    playlist_stats = PlaylistStats(my_music_lib, music_util, print)

    seed_prefix = "seed: "
    seed_playlists = my_music_lib.search_my_playlists(seed_prefix)
    print(f"Found {len(seed_playlists)} matching playlists.")

    # TODO: replace all of this with a single call to playlist_updater.update_my_seed_playlists
    for seed_playlist in seed_playlists:
        playlist_updater = PlaylistUpdater(
            my_music_lib,
            music_util,
            spotify,
            print,
            playlist_stats
        )
        get_target_playlist_name = lambda seed_playlist_name: seed_playlist_name[len(seed_prefix):]
        updated_playlist = playlist_updater.create_or_update_target_from_seed(
            seed_playlist, 3, get_target_playlist_name)
        if updated_playlist is not None:
            print(f"Updated '{updated_playlist.name}'.")


if __name__ == "__main__":
    main()