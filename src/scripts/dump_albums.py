# allows me to run:
# $ python scripts/dump_albums.py
import sys
sys.path.extend(['.', '../'])

from packages.music_management.music_util import MusicUtil
from packages.music_api_clients.spotify_client_wrapper import SpotifyClientWrapper


def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper, print)

    matching_artists = spotify_client_wrapper.get_matching_artists("beatles")
    artist = music_util.get_most_popular_artist(matching_artists)
    for album in spotify_client_wrapper.get_artist_albums(artist.id):
        print(album.name)


if __name__ == "__main__":
    main()