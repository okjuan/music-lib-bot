# allows me to run:
# $ python scripts/dump_albums.py
import sys
sys.path.extend(['.', '../'])

from app.lib.music_util import MusicUtil
from app.lib.spotify_client_wrapper import SpotifyClientWrapper


def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    #my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)

    matching_artists = spotify_client_wrapper.get_matching_artists("beatles")
    artist = music_util.get_most_popular_artist(matching_artists)
    for album in spotify_client_wrapper.get_artist_albums(artist.id):
        print(album.name)


if __name__ == "__main__":
    main()