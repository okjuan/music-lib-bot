# allows me to run:
# $ python scripts/dump_albums.py
import sys
sys.path.extend(['.', '../'])

from packages.music_management.music_util import MusicUtil
from packages.music_api_clients.spotify import Spotify


def main():
    spotify = Spotify()
    music_util = MusicUtil(spotify, print)

    matching_artists = spotify.get_matching_artists("beatles")
    artist = music_util.get_most_popular_artist(matching_artists)
    for album in spotify.get_artist_albums(artist.spotify_id):
        print(album.name)


if __name__ == "__main__":
    main()