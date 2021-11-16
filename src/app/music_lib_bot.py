# allows me to run:
# $ python scripts/music_lib_bot.py
import sys

sys.path.extend(['.', '../'])

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.lib.music_lib_bot_helper import MusicLibBotHelper
from app.playlist_updater import PlaylistUpdater
from app.lib.spotify_client_wrapper import SpotifyClientWrapper
from app.lib.ui import ConsoleUI
from app.playlist_creator import PlaylistCreator

DEFAULT_NUM_TRACKS_PER_ALBUM = 3
MIN_NUM_TRACKS_PER_ALBUM = 1
MAX_NUM_TRACKS_PER_ALBUM = 10
DEFAULT_NUM_ALBUMS_TO_FETCH = 50


class MusicLibBot:
    def __init__(self, spotify_client, my_music_lib, music_util, ui):
        self.spotify_client = spotify_client
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.ui = ui
        self.playlist_creator = PlaylistCreator(
            self.spotify_client,
            MusicLibBotHelper(self.my_music_lib, self.ui),
            self.my_music_lib,
            self.music_util,
            self.ui.tell_user,
        )

    def run_playlist_updater(self):
        while True:
            playlist = self.get_playlist_from_user()
            playlist_updater = PlaylistUpdater(
                playlist,
                self.my_music_lib,
                self.music_util,
            )
            playlist_updater.add_tracks_from_my_saved_albums_with_similar_genres__lazy(
                self.get_num_tracks_per_album, self.get_num_albums_to_fetch)

            if not self.user_wants_to_continue():
                break
        self.ui.tell_user(f"Thanks for using Playlist Updater, catch ya next time.")

    def user_wants_to_continue(self):
        return self.ui.get_yes_or_no("Make more changes? y or no - default is 'n'", False)

    def get_playlist_from_user(self):
        playlist = None
        while playlist is None:
            playlist_name = self.ui.get_non_empty_string(
                "What's the name of your playlist?")
            playlist = self.my_music_lib.get_playlist_by_name(playlist_name)
            if playlist is None:
                self.ui.tell_user(f"I couldn't find '{playlist_name}' in your playlists.")
        return playlist

    def get_num_tracks_per_album(self):
        return self.ui.get_int_from_range(
            f"# of tracks per album to add to playlist? default is {DEFAULT_NUM_TRACKS_PER_ALBUM}",
            DEFAULT_NUM_TRACKS_PER_ALBUM,
            MIN_NUM_TRACKS_PER_ALBUM,
            MAX_NUM_TRACKS_PER_ALBUM
        )

    def get_num_albums_to_fetch(self):
        return self.ui.get_int(
            f"# of albums to fetch from your library? default is {DEFAULT_NUM_ALBUMS_TO_FETCH}",
            DEFAULT_NUM_ALBUMS_TO_FETCH
        )

    def _get_artist_from_user(self):
        artist_name = self.ui.get_non_empty_string("What artist interests you?")
        matching_artists = self.spotify_client.get_matching_artists(artist_name)
        if matching_artists == []:
            self.ui.tell_user(f"Sorry, I couldn't find an artist by the name '{artist_name}'")
            return None
        artist = self.music_util.get_most_popular_artist(matching_artists)
        self.ui.tell_user(f"I found: {artist.name}, with genres {artist.genres}, with popularity {artist.popularity}")
        return artist

    def _get_create_playlist_from_an_artists_discography_callback(self):
        get_num_tracks_per_album = lambda: self.ui.get_int_from_options(
                "How many tracks do you want from each album?", [1, 2, 3, 4, 5])
        get_new_playlist_name = lambda: self.ui.get_non_empty_string(
            "What do you want to call your playlist?")
        def callback():
            self.playlist_creator.create_playlist_from_an_artists_discography(
                self._get_artist_from_user,
                get_num_tracks_per_album,
                get_new_playlist_name,
            )
        return callback

    def _get_create_playlist_based_on_existing_playlist_callback(self):
        get_new_playlist_name = lambda: self.ui.get_non_empty_string(
            "What should your new playlist be called?")
        get_num_tracks_per_album = lambda: self.ui.get_int(
            f"How many tracks per album? default is {DEFAULT_NUM_TRACKS_PER_ALBUM}",
            DEFAULT_NUM_TRACKS_PER_ALBUM
        )
        def callback():
            self.playlist_creator.create_playlist_based_on_existing_playlist(
                get_new_playlist_name,
                get_num_tracks_per_album,
            )
        return callback

    def run(self):
        functions = {
            "a": self.playlist_creator.run,
            "b": self._get_create_playlist_from_an_artists_discography_callback(),
            "c": self._get_create_playlist_based_on_existing_playlist_callback(),
            "d": self.run_playlist_updater,
        }
        menu = [
            "What d'ya wanna do? Pick an option:",
            "Create a playlist:",
            "'a' - Playlist Creator",
            "'b' - Create playlist from an artist's discography",
            "'c' - Duplicate a playlist full of albums, reduce its tracks per album, and reshuffle the order.",
            "",
            "Update a playlist:",
            "'d' - Add tracks to my playlist from my saved albums with similar genres",
            "",
            "'q' - quit",
        ]
        options = ["a", "b", "c", "d", "q"]
        while True:
            selection = self.ui.get_string_from_options(
                "\n\t".join(menu), options)
            if selection == 'q':
                self.ui.tell_user("Happy listening!")
                break
            functions[selection]()


def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)
    ui = ConsoleUI()
    MusicLibBot(spotify_client_wrapper, my_music_lib, music_util, ui).run()


if __name__ == "__main__":
    main()