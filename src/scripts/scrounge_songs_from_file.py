# allows me to run:
# $ python scripts/dump_albums.py
import sys
sys.path.extend(['.', '../'])

from packages.music_api_clients.spotify import Spotify
from packages.song_scrounger.song_scrounger import SongScrounger
from scrounge_helper import print_summary_of_song_matches


def main():
    spotify = Spotify()
    song_scrounger = SongScrounger(spotify)
    file_name = input("Enter the relative path to a file and I'll look at it and find songs mentioned in it: ")

    print("\nScanning for songs...")
    songs = song_scrounger.find_songs_in_text_file(file_name)

    print_summary_of_song_matches(songs)


if __name__ == "__main__":
    main()