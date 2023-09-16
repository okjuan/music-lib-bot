# allows me to run:
# $ python scripts/playlist_updater_example.py
import sys

sys.path.extend(['.', '../'])

from packages.music_management.music_util import MusicUtil
from packages.music_management.my_music_lib import MyMusicLib
from packages.music_api_clients.spotify import Spotify

def main():
    spotify = Spotify()
    playlists = spotify.get_all_user_playlists("2222rxc7a5xacexelkeqbrony")
    if (len(playlists) == 0):
        print("No playlists found")
        return

    music_util = MusicUtil(spotify, print)
    my_music_lib = MyMusicLib(spotify, music_util, print)
    for playlist in playlists:
        new_playlist_name = f"Jaime: {playlist.name}"
        print(f"Creating playlist: \"{new_playlist_name}\", containing ", len(playlist.get_tracks()), " tracks")
        my_music_lib.create_playlist(
            new_playlist_name,
            playlist.get_tracks(),
            playlist.description
        )


if __name__ == "__main__":
    main()