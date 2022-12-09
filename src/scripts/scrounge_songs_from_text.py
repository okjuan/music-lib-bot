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
    text = input("""Enter text below and I'll find the songs in it\ne.g. From the rubberized low end of "Señorita" to the nightcored hyperventilation that shakes "Skullqueen," Arca gives into her most brutal impulses.\n--------\n""")

    print("\nScanning for songs...")
    songs = song_scrounger.find_songs(text)

    print_summary_of_song_matches(songs)


if __name__ == "__main__":
    main()