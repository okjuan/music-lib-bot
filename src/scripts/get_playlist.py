# allows me to run:
# $ python scripts/playlist_updater_example.py
import sys

sys.path.extend(['.', '../'])

from packages.music_api_clients.spotify import Spotify
from packages.music_api_clients.models.playlist import Playlist

def main():
    spotify = Spotify()
    playlist = spotify.get_playlist(
        Playlist('', '', lambda: [], spotify_id='1A9sxywTENaMyK0mIlWlkm'))
    pass


if __name__ == "__main__":
    main()