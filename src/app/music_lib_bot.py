# allows me to run:
# $ python scripts/music_lib_bot.py
import sys

sys.path.extend(['.', '../'])

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.playlist_updater import PlaylistUpdater
from app.lib.spotify_client_wrapper import SpotifyClientWrapper
from app.lib.ui import ConsoleUI
from app.playlist_creator import PlaylistCreator

QUIT = -1
DEFAULT_LOOK_AT_ENTIRE_LIBRARY = False
DEFAULT_MIN_ALBUMS_PER_PLAYLIST = 4
DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST = 4
DEFAULT_MIN_GENRES_PER_PLAYLIST = 4
DEFAULT_NUM_TRACKS_PER_ALBUM = 3
DEFAULT_NUM_ALBUMS_TO_FETCH = 50
MIN_PLAYLIST_SUGGESTIONS_TO_SHOW = 10
MIN_NUM_TRACKS_PER_ALBUM = 1
MAX_NUM_TRACKS_PER_ALBUM = 10


class MusicLibBot:
    def __init__(self, spotify_client, my_music_lib, music_util, ui):
        self.spotify_client = spotify_client
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.ui = ui
        self.playlist_creator = PlaylistCreator(
            self.spotify_client,
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

    def get_min_albums_per_playlist(self):
        return self.ui.get_int(
            f"Minimum # of albums per playlist? default is {DEFAULT_MIN_ALBUMS_PER_PLAYLIST}",
            DEFAULT_MIN_ALBUMS_PER_PLAYLIST
        )

    def get_min_artists_per_playlist(self):
        return self.ui.get_int(
            f"Minimum # of artists per playlist? default is {DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST}",
            DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST
        )

    def get_min_genres_per_group(self):
        return self.ui.get_int(
            f"Minimum # of genres per playlist? default is {DEFAULT_MIN_GENRES_PER_PLAYLIST}",
            DEFAULT_MIN_GENRES_PER_PLAYLIST
        )

    def look_at_entire_library(self):
        return self.ui.get_yes_or_no(
            f"Should I look at your entire library? y or n - default is {'y' if DEFAULT_LOOK_AT_ENTIRE_LIBRARY else 'n'}",
            DEFAULT_LOOK_AT_ENTIRE_LIBRARY
        )

    def user_wants_to_create_another_playlist(self):
        return self.ui.get_yes_or_no(
            f"Create another playlist? y or n - default is 'y'",
            True
        )

    def get_num_diff_artists(self, albums):
        return len({
            artist.id
            for album in albums
            for artist in album.artists
        })

    def get_num_options_desired(self, options):
        if len(options) <= MIN_PLAYLIST_SUGGESTIONS_TO_SHOW:
            return len(options)

        min_option, max_option = 1, len(options)
        message = f"How many playlist options do you want to see?\n\t(Enter a number between {min_option} and {max_option})\n"
        return self.ui.get_int_from_range(
            message,
            min(max_option, MIN_PLAYLIST_SUGGESTIONS_TO_SHOW),
            min_option,
            max_option
        )

    def _get_indices_as_list(self, list_):
        return list(range(len(list_)))

    def get_num_tracks_per_album(self):
        return self.ui.get_int(
            f"How many tracks per album per playlist? default is {DEFAULT_NUM_TRACKS_PER_ALBUM}",
            DEFAULT_NUM_TRACKS_PER_ALBUM
        )

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
                self.get_playlist_from_user,
                get_new_playlist_name,
                get_num_tracks_per_album,
            )
        return callback

    def get_albums_by_genre(self):
        min_genres_per_group = self.get_min_genres_per_group()
        if self.look_at_entire_library():
            albums_by_genre = self.my_music_lib.get_all_my_albums_grouped_by_genre(
                min_genres_per_group)
        else:
            albums_by_genre = self.my_music_lib.get_my_albums_grouped_by_genre(
                self.get_num_albums_to_fetch(), min_genres_per_group)
        return albums_by_genre

    def get_suggested_playlists(self, albums_by_genre):
        min_albums_per_playlist = self.get_min_albums_per_playlist()
        min_artists_per_playlist = self.get_min_artists_per_playlist()
        playlist_criteria = lambda albums: len(albums) >= min_albums_per_playlist and self.get_num_diff_artists(albums) >= min_artists_per_playlist
        return [
            dict(
                description=', '.join(album_group['genres']),
                albums=album_group['albums']
            )
            for album_group in albums_by_genre
            if playlist_criteria(album_group['albums'])
        ]

    def interatively_create_playlists_from_my_albums_with_matching_genres(self):
        albums_by_genre = self.get_albums_by_genre()
        if len(albums_by_genre) == 0:
            self.ui.tell_user("Couldn't match the albums into groups.. the genres didn't match :/")
            return

        suggested_playlists = self.get_suggested_playlists(albums_by_genre)
        if len(suggested_playlists) == 0:
            self.ui.tell_user("Couldn't find any suggested playlists!")
            return

        self.launch_interactive_playlist_creator(suggested_playlists)

    def launch_interactive_playlist_creator(self, suggested_playlists):
        while True:
            selection = self.get_selection(suggested_playlists)
            if selection is QUIT:
                self.ui.tell_user("Quitting...")
                break

            self.playlist_creator.create_playlist_from_albums(
                suggested_playlists[selection], self.get_num_tracks_per_album)
            if not self.user_wants_to_create_another_playlist():
                break

    def get_selection(self, suggested_playlists):
        num_options = self.get_num_options_desired(suggested_playlists)
        min_option, max_option = 0, len(suggested_playlists)-1
        message = f"Please select which playlist to create!\nEnter a number between {min_option} and {max_option} or enter {QUIT} to quit:"
        self.give_playlist_options(num_options, suggested_playlists)
        options = [QUIT, *self._get_indices_as_list(suggested_playlists)]
        return self.ui.get_int_from_options(message, options)

    def give_playlist_options(self, num_options, options):
        # TODO: remove/replace \n, \t chars, etc.
        self.ui.tell_user("\nHere are your options for creating a playlist from albums in your library.")
        self.ui.tell_user("The options are ordered by number of albums from most to least.")
        options.sort(
            key=lambda album_group: len(album_group['albums']),
            reverse=True
        )
        for idx, album_group in enumerate(options[:num_options]):
            artists = list({artist.name for album in album_group['albums'] for artist in album.artists})
            self.ui.tell_user(f"#{idx}\n\tDescription: {album_group['description']}\n\tNumber of albums: {len(album_group['albums'])}\n\tArtists: {', '.join(artists)}")

    def run(self):
        functions = {
            "a": self._get_create_playlist_from_an_artists_discography_callback(),
            "b": self._get_create_playlist_based_on_existing_playlist_callback(),
            "c": self.interatively_create_playlists_from_my_albums_with_matching_genres,
            "d": self.run_playlist_updater,
        }
        menu = [
            "What d'ya wanna do? Pick an option:",
            "Create a playlist:",
            "'a' - from an artist's discography",
            "'b' - from a playlist full of albums.",
            "'c' - (interactive) from albums in your library that have matching genres.",
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