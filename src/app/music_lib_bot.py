# allows me to run:
# $ python app/music_lib_bot.py
import sys
sys.path.extend(['.', '../'])

from packages.music_management.music_util import MusicUtil
from packages.music_management.my_music_lib import MyMusicLib
from packages.music_management.playlist_creator import PlaylistCreator
from packages.music_management.playlist_analyzer import PlaylistAnalyzer
from packages.music_management.playlist_updater import PlaylistUpdater
from app.lib.interactive_option_picker import InteractiveOptionPicker
from packages.music_api_clients.spotify import Spotify
from app.lib.console_ui import ConsoleUI

DEFAULT_LOOK_AT_ENTIRE_LIBRARY = False
DEFAULT_MIN_ALBUMS_PER_PLAYLIST = 4
DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST = 4
DEFAULT_MIN_GENRES_PER_PLAYLIST = 4
DEFAULT_NUM_TRACKS_PER_ALBUM = 3
DEFAULT_NUM_ALBUMS_TO_FETCH = 50
MIN_NUM_TRACKS_PER_ALBUM = 1
MAX_NUM_TRACKS_PER_ALBUM = 10
DEFAULT_NUM_TRACKS_TO_ADD = 0
MIN_NUM_TRACKS_TO_ADD = 1
MAX_NUM_TRACKS_TO_ADD = 100
DEFAULT_SEED_PREFIX = "seed: "


class MusicLibBot:
    """This is an interactive app for music library management. It presents the user
    with options for creating and updating playlists and prompts them for parameters
    such as the number of songs per album to add to a playlist.

    The goal of this module is to interact with a user to allow them to configure and
    issue commands. However, it should be possible to run the same commands in other
    modules. Hence, there should be little-to-no command logic here. All command-specific
    logic should exist in other modules which are imported here e.g. PlaylistUpdater.

    For example, notice that `run_create_or_update_target_from_seed` literally runs
    `create_or_update_target_from_seed`. All other logic in that function is for
    collecting configuration parameters from the user and informing the user.
    """

    def __init__(self, music_api_client, my_music_lib, music_util, ui):
        self.music_api_client = music_api_client
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.ui = ui
        self.playlist_creator = PlaylistCreator(
            self.music_api_client,
            self.my_music_lib,
            self.music_util,
            self.ui.tell_user,
        )
        self.playlist_analyzer = PlaylistAnalyzer(
            self.my_music_lib,
            self.music_util,
            self.ui.tell_user,
        )

    def run_create_or_update_target_from_seed(self):
        self.ui.tell_user("Let's update target playlists from seed playlists.")
        messages = [
            "",
            "Ok, so this is how this works..",
            "First, I'll find all your playlists that have a certain prefix in their name...",
            "Then, for each of them, I'll create a 'target' playlist",
            "(or find an existing one because I may have done this for you in the past.)",
            "A target playlist is named the same as its seed playlist minus the prefix.",
            "Then I'll add songs from the seed to the target, avoiding duplicates!",
        ]
        self.ui.tell_user("\n".join(messages))
        seed_prefix = self.ui.get_string(
            f"What's your seed prefix? (default is '{DEFAULT_SEED_PREFIX}')", DEFAULT_SEED_PREFIX)
        self.ui.tell_user(f"Ok, gonna look for playlists that look like '{seed_prefix}blah blah'")

        seed_playlists = self.my_music_lib.search_my_playlists(seed_prefix)
        if len(seed_playlists) == 0:
            self.ui.tell_user("No seed playlists found!")
            return
        self.ui.tell_user(f"Found {len(seed_playlists)} matching playlists.")

        num_tracks_per_album = self.ui.get_int(
            f"How many tracks per album do you want in the target playlist? default is {DEFAULT_NUM_TRACKS_PER_ALBUM}",
            DEFAULT_NUM_TRACKS_PER_ALBUM
        )
        updates = PlaylistUpdater(
            self.my_music_lib,
            self.music_util,
            self.music_api_client,
            self.ui.tell_user,
            self.playlist_analyzer,
        ).create_or_update_all_targets_from_seeds(
            seed_playlists,
            num_tracks_per_album,
            lambda seed_playlist: seed_playlist.name[len(seed_prefix):],
        )

        no_playlist_was_updated = True
        for update in updates:
            if update[1] > 0:
                no_playlist_was_updated = False
                self.ui.tell_user(f"Added {update[1]} songs to playlist '{update[0].name}'.")
            else:
                self.ui.tell_user(f"Playlist '{update[0].name}' did not need any updates.")
        if no_playlist_was_updated:
            self.ui.tell_user("Didn't update any playlists!")

    def run_add_tracks_from_my_saved_albums_with_similar_genres(self):
        self.ui.tell_user("Let's update an existing playlist with tracks from my saved albums with similar genres.")
        playlist = self._get_playlist_from_user(
            self.my_music_lib.get_playlist_by_name)
        playlist_updater = PlaylistUpdater(
            self.my_music_lib,
            self.music_util,
            self.music_api_client,
            self.ui.tell_user,
            self.playlist_analyzer,
        )
        num_tracks_added = playlist_updater.add_tracks_from_my_saved_albums_with_same_genres(
            playlist,
            self._get_num_tracks_per_album,
            self._get_num_albums_to_fetch,
        )
        if num_tracks_added > 0:
            return
        self.ui.tell_user("Will try to add songs with similar genres..")
        playlist_updater.add_tracks_from_my_saved_albums_with_similar_genres(
            playlist,
            self._get_num_tracks_per_album,
            self._get_num_albums_to_fetch,
        )

    def run_add_recommended_tracks_with_similar_attributes(self):
        self.ui.tell_user("Let's update an existing playlist with recommended tracks with similar attributes.")
        playlist = self._get_playlist_from_user(
            self.my_music_lib.get_playlist_by_name)
        self.music_util.populate_track_audio_features(playlist)
        song_attribute_ranges = self.music_util.get_lenient_song_attribute_ranges(
            playlist)
        recommended_tracks_by_percentage = self.music_util.get_recommendations_based_on_tracks(
            playlist.get_tracks(), song_attribute_ranges)
        if len(recommended_tracks_by_percentage) == 0:
            self.ui.tell_user("Sorry, couldn't find recommendations to add :(")
            return
        recommended_tracks_with_percentage = sorted(
            [
                dict(
                    recommended_percentage=recommended_percentage,
                    tracks=tracks
                )
                for recommended_percentage, tracks in recommended_tracks_by_percentage.items()
            ],
            key=lambda x: x["recommended_percentage"],
            reverse=True
        )

        def recommended_track_pick_handler(recommended_tracks_with_percentage):
            self.my_music_lib.add_tracks_to_playlist(
                playlist, recommended_tracks_with_percentage["tracks"])

        def get_recommended_track_description(recommended_tracks_with_percentage):
            percentage = int(recommended_tracks_with_percentage['recommended_percentage'] * 100)
            preamble = f"Recommended with {percentage}% confidence:\n- "
            return preamble + "\n- ".join([
                f"{track.name} by {', '.join([artist.name for artist in track.artists])}"
                for track in recommended_tracks_with_percentage['tracks']
            ])
        InteractiveOptionPicker(
            recommended_tracks_with_percentage,
            recommended_track_pick_handler,
            self.ui,
            get_recommended_track_description,
        ).run()

    def run_interactive_playlist_picker(self):
        self.ui.tell_user("Let's create a playlist from albums in your library that have matching genres.")
        suggested_playlists = self._get_playlist_options()
        if len(suggested_playlists) == 0:
            self.ui.tell_user("Couldn't find any suggested playlists!")
            return
        def playlist_pick_handler(playlist):
            return self.playlist_creator.create_playlist_from_albums(
                playlist, self._get_num_tracks_per_album)
        InteractiveOptionPicker(
            suggested_playlists,
            playlist_pick_handler,
            self.ui,
            self._get_playlist_description,
        ).run()

    def run_create_playlist_from_an_artists_discography(self):
        self.ui.tell_user("Let's create a playlist from an artist's discography.")
        _get_num_tracks_per_album = lambda: self.ui.get_int_from_options(
                "How many tracks do you want from each album?", [1, 2, 3, 4, 5])
        get_new_playlist_name = lambda: self.ui.get_non_empty_string(
            "What do you want to call your playlist?")
        self.playlist_creator.create_playlist_from_an_artists_discography(
            self._get_artist_from_user,
            _get_num_tracks_per_album,
            get_new_playlist_name,
        )

    def run_create_playlist_based_on_existing_playlist(self):
        self.ui.tell_user("Let's create a playlist from a playlist full of albums.")
        get_new_playlist_name = lambda: self.ui.get_non_empty_string(
            "What should your new playlist be called?")
        _get_num_tracks_per_album = lambda: self.ui.get_int(
            f"How many tracks per album? default is {DEFAULT_NUM_TRACKS_PER_ALBUM}",
            DEFAULT_NUM_TRACKS_PER_ALBUM
        )
        self.playlist_creator.create_playlist_based_on_existing_playlist(
            lambda: self._get_playlist_from_user(
                self.my_music_lib.get_playlist_by_name),
            get_new_playlist_name,
            _get_num_tracks_per_album,
        )

    def run(self):
        options = {
            "a": "Create playlist from an artist's discography.",
            "b": "Create playlist from a playlist full of albums.",
            "c": "Update target playlists from seed playlists.",
            "d": "Create playlist from albums in your library that have matching genres.",
            "e": "Update existing playlist with tracks from my saved albums with similar genres.",
            "f": "Update existing playlist with recommended tracks with similar attributes.",
        }
        functions = {
            "a": self.run_create_playlist_from_an_artists_discography,
            "b": self.run_create_playlist_based_on_existing_playlist,
            "c": self.run_create_or_update_target_from_seed,
            "d": self.run_interactive_playlist_picker,
            "e": self.run_add_tracks_from_my_saved_albums_with_similar_genres,
            "f": self.run_add_recommended_tracks_with_similar_attributes,
        }
        def option_pick_handler(pick):
            functions[pick]()
        def get_option_description(pick):
            return options[pick]
        InteractiveOptionPicker(
            list(options.keys()),
            option_pick_handler,
            self.ui,
            get_option_description,
        ).run()

    def _get_playlist_from_user(self, get_playlist_by_name):
        playlist = None
        while playlist is None:
            playlist_name = self.ui.get_non_empty_string(
                "What's the name of your playlist?")
            playlist = get_playlist_by_name(playlist_name)
            if playlist is None:
                self.ui.tell_user(f"I couldn't find '{playlist_name}' in your playlists.")
        return playlist

    def _get_num_tracks_to_add(self):
        return self.ui.get_int_from_range(
            f"# of tracks to add to playlist?",
            DEFAULT_NUM_TRACKS_TO_ADD,
            MIN_NUM_TRACKS_TO_ADD,
            MAX_NUM_TRACKS_TO_ADD
        )

    def _get_num_tracks_per_album(self):
        return self.ui.get_int_from_range(
            f"# of tracks per album to add to playlist? default is {DEFAULT_NUM_TRACKS_PER_ALBUM}",
            DEFAULT_NUM_TRACKS_PER_ALBUM,
            MIN_NUM_TRACKS_PER_ALBUM,
            MAX_NUM_TRACKS_PER_ALBUM
        )

    def _get_num_albums_to_fetch(self):
        return self.ui.get_int(
            f"# of albums to fetch from your library? default is {DEFAULT_NUM_ALBUMS_TO_FETCH}",
            DEFAULT_NUM_ALBUMS_TO_FETCH
        )

    def _get_min_albums_per_playlist(self):
        return self.ui.get_int(
            f"Minimum # of albums per playlist? default is {DEFAULT_MIN_ALBUMS_PER_PLAYLIST}",
            DEFAULT_MIN_ALBUMS_PER_PLAYLIST
        )

    def _get_min_artists_per_playlist(self):
        return self.ui.get_int(
            f"Minimum # of artists per playlist? default is {DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST}",
            DEFAULT_MIN_NUM_ARTISTS_PER_PLAYLIST
        )

    def _get_min_genres_per_group(self):
        return self.ui.get_int(
            f"Minimum # of genres per playlist? default is {DEFAULT_MIN_GENRES_PER_PLAYLIST}",
            DEFAULT_MIN_GENRES_PER_PLAYLIST
        )

    def _look_at_entire_library(self):
        return self.ui.get_yes_or_no(
            f"Should I look at your entire library? y or n - default is {'y' if DEFAULT_LOOK_AT_ENTIRE_LIBRARY else 'n'}",
            DEFAULT_LOOK_AT_ENTIRE_LIBRARY
        )

    def _get_albums_by_genre(self):
        min_genres_per_group = self._get_min_genres_per_group()
        if self._look_at_entire_library():
            albums_by_genre = self.my_music_lib.get_all_my_albums_grouped_by_genre(
                min_genres_per_group)
        else:
            albums_by_genre = self.my_music_lib.get_my_albums_grouped_by_genre(
                self._get_num_albums_to_fetch(), min_genres_per_group)
        return albums_by_genre

    def _get_suggested_playlists(self, albums_by_genre):
        """
        Returns:
            ([dict]): each with 2 key-value pairs:
                key "description", value (str).
                key "albums", value ([Album]).
        """
        min_albums_per_playlist = self._get_min_albums_per_playlist()
        min_artists_per_playlist = self._get_min_artists_per_playlist()
        playlist_criteria = lambda albums: len(albums) >= min_albums_per_playlist and self.music_util.get_num_diff_artists(albums) >= min_artists_per_playlist
        return [
            dict(
                description=', '.join(album_group['genres']),
                albums=album_group['albums']
            )
            for album_group in albums_by_genre
            if playlist_criteria(album_group['albums'])
        ]

    def _get_playlist_options(self):
        """
        Returns:
            ([dict]): each dict with 2 key-value pairs:
                - key "description", value (str).
                - key "albums", value ([Album]).
                sorted in descending order by number of albums,
        """
        albums_by_genre = self._get_albums_by_genre()
        if len(albums_by_genre) == 0:
            self.ui.tell_user("Couldn't match the albums into groups.. the genres didn't match :/")
            return

        return sorted(
            self._get_suggested_playlists(albums_by_genre),
            key=lambda album_group: len(album_group['albums']),
            reverse=True
        )

    def _get_artist_from_user(self):
        artist_name = self.ui.get_non_empty_string("What artist interests you?")
        matching_artists = self.music_api_client.get_matching_artists(artist_name)
        if matching_artists == []:
            self.ui.tell_user(f"Sorry, I couldn't find an artist by the name '{artist_name}'")
            return None
        artist = self.music_util.get_most_popular_artist(matching_artists)
        self.ui.tell_user(f"I found: {artist.name}, with genres {artist.genres}, with popularity {artist.popularity}")
        return artist

    def _get_playlist_description(self, album_group):
        artists = list({
            artist.name
            for album in album_group['albums']
            for artist in album.artists
        })
        return "\n\t".join([
            f"Description: {album_group['description']}",
            f"Number of albums: {len(album_group['albums'])}",
            f"Artists: {', '.join(artists)}",
        ])


def main():
    spotify = Spotify()
    ui = ConsoleUI()
    music_util = MusicUtil(spotify, ui.tell_user)
    my_music_lib = MyMusicLib(spotify, music_util, ui.tell_user)
    MusicLibBot(spotify, my_music_lib, music_util, ui).run()


if __name__ == "__main__":
    main()