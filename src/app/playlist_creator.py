# allows me to run:
# $ python app/playlist_creator.py
import sys
sys.path.extend(['.', '../'])

from collections import defaultdict
from random import shuffle

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.lib.spotify_client_wrapper import SpotifyClientWrapper
from app.lib.ui import ConsoleUI


QUIT = -1
DEFAULT_ALBUMS_TO_FETCH = 50
DEFAULT_LOOK_AT_ENTIRE_LIBRARY = False
DEFAULT_NUM_TRACKS_PER_ALBUM = 3
DEFAULT_MIN_ALBUMS_PER_PLAYLIST = 4
DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST = 4
DEFAULT_MIN_GENRES_PER_PLAYLIST = 4
MIN_PLAYLIST_SUGGESTIONS_TO_SHOW = 10

class PlaylistCreator:
    def __init__(self, spotify_client, music_lib_bot_helper, my_music_lib, music_util, ui):
        self.spotify_client = spotify_client
        self.music_lib_bot_helper = music_lib_bot_helper
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.ui = ui

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

    def get_selection(self, suggested_playlists):
        num_options = self.get_num_options_desired(suggested_playlists)
        min_option, max_option = 0, len(suggested_playlists)-1
        message = f"Please select which playlist to create!\nEnter a number between {min_option} and {max_option} or enter {QUIT} to quit:"
        self.give_playlist_options(num_options, suggested_playlists)
        options = [QUIT, *self._get_indices_as_list(suggested_playlists)]
        return self.ui.get_int_from_options(message, options)

    def _get_indices_as_list(self, list_):
        return list(range(len(list_)))

    def get_num_tracks_per_album(self):
        return self.ui.get_int(
            f"How many tracks per album per playlist? default is {DEFAULT_NUM_TRACKS_PER_ALBUM}",
            DEFAULT_NUM_TRACKS_PER_ALBUM
        )

    def create_playlist_from_albums(self, album_group):
        tracks = self.music_util.get_most_popular_tracks_from_each(
            album_group["albums"], self.get_num_tracks_per_album())
        shuffle(tracks)

        self.ui.tell_user(f"Creating '{album_group['description']}' playlist from {len(album_group['albums'])} albums...")
        self.my_music_lib.create_playlist(
            album_group["description"],
            [track.uri for track in tracks],
            description="created by playlist_creator"
        )
        self.ui.tell_user(f"Playlist created!")

    def launch_interactive_playlist_creator(self, suggested_playlists):
        while True:
            selection = self.get_selection(suggested_playlists)
            if selection is QUIT:
                self.ui.tell_user("Quitting...")
                break

            self.create_playlist_from_albums(suggested_playlists[selection])
            if not self.user_wants_to_create_another_playlist():
                break

    def get_num_diff_artists(self, albums):
        return len({
            artist.id
            for album in albums
            for artist in album.artists
        })

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

    def get_num_albums_to_fetch(self):
        return self.ui.get_int(
            f"# of albums to fetch from your library? default is {DEFAULT_ALBUMS_TO_FETCH}",
            DEFAULT_ALBUMS_TO_FETCH
        )

    def user_wants_to_create_another_playlist(self):
        return self.ui.get_yes_or_no(
            f"Create another playlist? y or n - default is 'y'",
            True
        )

    def get_albums_by_genre(self):
        min_genres_per_group = self.get_min_genres_per_group()
        if self.look_at_entire_library():
            albums_by_genre = self.my_music_lib.get_all_my_albums_grouped_by_genre(
                min_genres_per_group)
        else:
            albums_by_genre = self.my_music_lib.get_my_albums_grouped_by_genre(
                self.get_num_albums_to_fetch(), min_genres_per_group)
        return albums_by_genre

    def create_playlist_based_on_existing_playlist(self):
        playlist = self.music_lib_bot_helper.get_playlist_from_user()
        new_playlist_name = self.ui.get_non_empty_string("What should your new playlist be called?")
        num_tracks_per_album = self.ui.get_int(
            f"How many tracks per album do you want in your new playlist? default is {DEFAULT_NUM_TRACKS_PER_ALBUM}",
            DEFAULT_NUM_TRACKS_PER_ALBUM
        )
        self.duplicate_and_reduce_num_tracks_per_album(
            playlist, new_playlist_name, num_tracks_per_album)

    def _get_artist_from_user(self):
        artist_name = self.ui.get_non_empty_string("What artist interests you?")
        matching_artists = self.spotify_client.get_matching_artists(artist_name)
        if matching_artists == []:
            self.ui.tell_user(f"Sorry, I couldn't find an artist by the name '{artist_name}'")
            return None
        artist = self.music_util.get_most_popular_artist(matching_artists)
        self.ui.tell_user(f"I found: {artist.name}, with genres {artist.genres}, with popularity {artist.popularity}")
        return artist

    def _get_discography_for_artist_of_users_choice(self):
        artist = self._get_artist_from_user()
        if artist is None:
            return None
        albums = self.music_util.get_discography(artist)
        if albums is None or albums == []:
            return None
        return albums

    # TODO: should I be reusing/reappropriating create_playlist_from_albums()?
    def create_playlist_from_an_artists_discography(self):
        albums = self._get_discography_for_artist_of_users_choice()
        if albums is None:
            self.ui.tell_user("Aborting because I don't have any albums to work with!")
            return

        self.ui.tell_user(f"Out of the total {len(albums)} number of albums...")
        albums = self.music_util.filter_out_duplicates_demos_and_live_albums(albums)
        self.ui.tell_user(f"Only {len(albums)} are essential; the rest are duplicates, demos, and live albums.")

        albums = self.music_util.order_albums_chronologically(albums)
        num_tracks_per_album = self.ui.get_int_from_options(
            "How many tracks do you want from each album?", [1, 2, 3, 4, 5])

        # NOTE: do list comprehension here to ensure album order is preserved
        tracks = [
            track
            for album in albums
            for track in self.music_util.get_most_popular_tracks(album, num_tracks_per_album)
        ]

        playlist_title = self.ui.get_non_empty_string(
            "What do you want to call your playlist?")
        self.ui.tell_user(f"Creating '{playlist_title}' playlist...")
        self.my_music_lib.create_playlist(
            playlist_title,
            [track.uri for track in tracks],
            description="created by playlist_creator"
        )

        self.ui.tell_user(f"Playlist created!")
        return albums

    def create_playlist_from_albums_with_matching_genres_in_library(self):
        albums_by_genre = self.get_albums_by_genre()
        suggested_playlists = self.get_suggested_playlists(albums_by_genre)
        if len(suggested_playlists) == 0:
            self.ui.tell_user("Couldn't find any suggested playlists!")
            return
        self.launch_interactive_playlist_creator(suggested_playlists)

    def duplicate_and_reduce_num_tracks_per_album(self, playlist, new_playlist_name, num_tracks_per_album):
        tracks_by_album = defaultdict(list)
        for track in playlist.tracks:
            tracks_by_album[track.album_id].append(track)

        most_popular_tracks_per_album = []
        # TODO: use music_util.get_tracks_most_popular_first(album) ?
        for _, tracks in tracks_by_album.items():
            tracks_sorted_by_popularity = sorted(
                tracks, key=lambda track: track.popularity, reverse=True)
            most_popular_tracks_per_album.extend(
                tracks_sorted_by_popularity[:num_tracks_per_album])

        self.ui.tell_user(f"Created your new playlist '{new_playlist_name}' containing {len(most_popular_tracks_per_album)} tracks!")

        track_uris = [track.id for track in most_popular_tracks_per_album]
        shuffle(track_uris)
        self.my_music_lib.create_playlist(new_playlist_name, track_uris)

    def run(self):
        options = {
            "a": self.create_playlist_from_an_artists_discography,
            "b": self.create_playlist_from_albums_with_matching_genres_in_library,
            "c": self.create_playlist_based_on_existing_playlist,
        }
        while True:
            selection = self.ui.get_string_from_options(
                "What kind of playlist do you want to create? Pick an option:\n\t'a' - From an artist's whole discography \n\t'b' - From albums in your library that have matching genres\n\t'c' - Duplicate a playlist full of albums, reduce its tracks per album, and reshuffle the order.\n\t'q' - quit",
                ["a", "b", "c", "q"]
            )
            if selection == 'q':
                self.ui.tell_user(f"Thanks for using Playlist Creator, see ya later!")
                break
            options[selection]()



def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)
    ui = ConsoleUI()
    PlaylistCreator(
        spotify_client_wrapper,
        my_music_lib,
        music_util,
        ui
    ).run()


if __name__ == "__main__":
    main()