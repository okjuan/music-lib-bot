# allows me to run:
# $ python scripts/playlist_updater_example.py
import sys
sys.path.extend(['.', '../'])

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.playlist_updater import PlaylistUpdater
from app.lib.spotify_client_wrapper import SpotifyClientWrapper

NUM_TRACKS_PER_ALBUM = 3
NUM_ALBUMS_TO_FETCH = 25

def main():
    """Creates new playlist with arbitrary song and fills it with more tracks from albums with the same genres."""
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)

    playlist_name = "PlaylistUpdater Test Playlist"
    playlist = my_music_lib.create_playlist(
        playlist_name, ["spotify:track:7G3lxTsMfSx4yarMkfgnTC"])
    playlist = my_music_lib.get_playlist_by_id(playlist.id)
    if playlist is None:
        print(f"Couldn't create your playlist '{playlist_name}'")
        return

    playlist_updater = PlaylistUpdater(playlist, my_music_lib, music_util)
    playlist_updater.add_tracks_from_my_saved_albums_with_same_genres(
        NUM_TRACKS_PER_ALBUM, NUM_ALBUMS_TO_FETCH)


if __name__ == "__main__":
    main()