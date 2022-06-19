# allows me to run:
# $ python scripts/dump_playlist_genres.py
import sys
sys.path.extend(['.', '../'])

from packages.music_management.my_music_lib import MyMusicLib
from packages.music_management.music_util import MusicUtil
from packages.music_api_clients.spotify import Spotify

NUM_TRACKS_PER_ALBUM = 3


def main():
    spotify = Spotify()
    music_util = MusicUtil(spotify, print)
    my_music_lib = MyMusicLib(spotify, music_util, print)

    seed_playlists = my_music_lib.search_my_playlists("seed: ")
    print(f"Found {len(seed_playlists)} matching playlists.")

    for seed_playlist in seed_playlists:
        print("Checking for playlist", seed_playlist.name, seed_playlist.id)
        target_playlist_name = seed_playlist.name[len("seed: "):]
        target_playlist = my_music_lib.get_or_create_playlist(target_playlist_name)

        seed_albums = music_util.get_albums_in_playlist(seed_playlist)
        if target_playlist.get_num_tracks() > 0:
            current_albums = music_util.get_albums_in_playlist(target_playlist)
        else:
            current_albums = []

        albums_to_add = set(seed_albums) - set(current_albums)
        #albums_to_remove = set(current_albums) - set(seed_albums)

        if len(albums_to_add) > 0:
            print("Finding what tracks to add..")
            tracks_to_add = music_util.get_most_popular_tracks_from_each(
                albums_to_add, NUM_TRACKS_PER_ALBUM)
            print(f"Adding {len(tracks_to_add)} tracks.")
            my_music_lib.add_tracks_in_random_positions(
                target_playlist, [track.uri for track in tracks_to_add])
        else:
            print(f"Playlist '{target_playlist.name}' is all up-to-date!")

        #if len(albums_to_remove) > 0:
        #    print("Finding the tracks to remove..")
        #    tracks_to_remove = music_util.filter_out_if_not_in_albums(
        #        target_playlist.tracks, albums_to_remove)
        #    print(f"Removing {len(tracks_to_remove)} tracks.")
        #    my_music_lib.remove_tracks_from_playlist(
        #        target_playlist, [track.uri for track in tracks_to_remove])


if __name__ == "__main__":
    main()