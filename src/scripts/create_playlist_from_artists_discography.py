# allows me to run:
# $ python scripts/this_script.py
import sys
sys.path.extend(['.', '../'])

from packages.music_management.music_util import MusicUtil
from packages.music_management.my_music_lib import MyMusicLib
from packages.music_api_clients.spotify import Spotify
from packages.music_api_clients.models.artist import Artist
from packages.music_management.playlist_creator import PlaylistCreator


def main():
    spotify = Spotify()
    music_util = MusicUtil(spotify, print)
    my_music_lib = MyMusicLib(spotify, music_util, print)

    PlaylistCreator(
        spotify,
        my_music_lib,
        music_util,
        print,
    ).create_playlist_from_an_artists_discography(
        # https://open.spotify.com/artist/0tIODqvzGUoEaK26rK4pvX?si=8pEfwJ9ASkeB0-34aPx5xw
        lambda: Artist("Sun Ra", spotify_id="0tIODqvzGUoEaK26rK4pvX"),
        lambda: 1,
        lambda: "Test Playlist - Sun Ra Discography",
    )


if __name__ == "__main__":
    main()