from music_util import MusicUtil
from my_music_lib import MyMusicLib
from playlist_updater import PlaylistUpdater
from spotify_client_wrapper import SpotifyClientWrapper

NUM_TRACKS_PER_ALBUM = 5

def main():
    """Creates new playlist with arbitrary song and fills it with more tracks from albums with the same genres."""
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)

    playlist_names = ["daytime dad rock", "funk n soul", "stripped down americana"]
    for playlist_name in playlist_names:
        playlist = my_music_lib.get_playlist_by_name(playlist_name)
        if playlist is None:
            print(f"Couldn't create your playlist '{playlist_name}'")
            return

        playlist_updater = PlaylistUpdater(playlist, my_music_lib, music_util)
        playlist_updater.duplicate_and_reduce_num_tracks_per_album(NUM_TRACKS_PER_ALBUM, f"{playlist_name} - redux")


if __name__ == "__main__":
    main()