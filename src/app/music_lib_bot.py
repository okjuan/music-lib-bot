# allows me to run:
# $ python app/music_lib_bot.py
import sys
sys.path.extend(['.', '../'])

from packages.music_management.music_util import MusicUtil
from packages.music_management.my_music_lib import MyMusicLib
from packages.music_management.playlist_creator import PlaylistCreator
from packages.music_management.playlist_stats import PlaylistStats
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
        self.playlist_stats = PlaylistStats(
            self.my_music_lib,
            self.music_util,
            self.ui.tell_user,
        )

    def run_create_or_update_target_from_seed(self):
        messages = [
            "",
            "Ok, so this is how this works..",
            "First, I'll find all your playlists that have a certain prefix in their name...",
            "Then, for each of them, I'll create a 'target' playlist"
            "(or find an existing one because I may have done this for you in the past.)",
            "(A target playlist is named the same as its seed playlist minus the prefix.)",
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

        updated_playlists = []
        for seed_playlist in seed_playlists:
            playlist_updater = PlaylistUpdater(
                seed_playlist,
                self.my_music_lib,
                self.music_util,
                self.music_api_client,
                self.ui.tell_user,
                self.playlist_stats,
            )
            target_playlist = playlist_updater.create_or_update_target_from_seed(
                seed_playlists,
                num_tracks_per_album,
                lambda seed_playlist_name: seed_playlist_name[len(seed_prefix):],
            )
            if target_playlist is not None:
                updated_playlists += target_playlist
            del playlist_updater

        num_playlists_updated = len(updated_playlists)
        if num_playlists_updated > 0:
            summary_message = f"I updated {num_playlists_updated} playlists including '{updated_playlists[0].name}'"
            if num_playlists_updated > 1:
                summary_message += f" and '{updated_playlists[1].name}'"
        else:
            summary_message = "Didn't update any playlists!"
        self.ui.tell_user(summary_message + ".")

    def run_add_tracks_from_my_saved_albums_with_similar_genres(self):
        playlist = self.get_playlist_from_user(
            self.my_music_lib.get_playlist_by_name)
        playlist_updater = PlaylistUpdater(
            playlist,
            self.my_music_lib,
            self.music_util,
            self.music_api_client,
            self.ui.tell_user,
            self.playlist_stats,
        )
        num_tracks_added = playlist_updater.add_tracks_from_my_saved_albums_with_same_genres(
            self.get_num_tracks_per_album, self.get_num_albums_to_fetch)
        if num_tracks_added > 0:
            return
        self.ui.tell_user("Will try to add songs with similar genres..")
        playlist_updater.add_tracks_from_my_saved_albums_with_similar_genres(
            self.get_num_tracks_per_album, self.get_num_albums_to_fetch)

    def run_add_recommended_tracks_with_similar_attributes(self):
        playlist = self.get_playlist_from_user(
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
        ).launch_interactive_picker()

    def get_playlist_from_user(self, get_playlist_by_name):
        playlist = None
        while playlist is None:
            playlist_name = self.ui.get_non_empty_string(
                "What's the name of your playlist?")
            playlist = get_playlist_by_name(playlist_name)
            if playlist is None:
                self.ui.tell_user(f"I couldn't find '{playlist_name}' in your playlists.")
        return playlist

    def get_num_tracks_to_add(self):
        return self.ui.get_int_from_range(
            f"# of tracks to add to playlist?",
            DEFAULT_NUM_TRACKS_TO_ADD,
            MIN_NUM_TRACKS_TO_ADD,
            MAX_NUM_TRACKS_TO_ADD
        )

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
        """
        Returns:
            ([dict]): each with 2 key-value pairs:
                key "description", value (str).
                key "albums", value ([Album]).
        """
        min_albums_per_playlist = self.get_min_albums_per_playlist()
        min_artists_per_playlist = self.get_min_artists_per_playlist()
        playlist_criteria = lambda albums: len(albums) >= min_albums_per_playlist and self.music_util.get_num_diff_artists(albums) >= min_artists_per_playlist
        return [
            dict(
                description=', '.join(album_group['genres']),
                albums=album_group['albums']
            )
            for album_group in albums_by_genre
            if playlist_criteria(album_group['albums'])
        ]

    def get_playlist_options(self):
        """
        Returns:
            ([dict]): each dict with 2 key-value pairs:
                - key "description", value (str).
                - key "albums", value ([Album]).
                sorted in descending order by number of albums,
        """
        albums_by_genre = self.get_albums_by_genre()
        if len(albums_by_genre) == 0:
            self.ui.tell_user("Couldn't match the albums into groups.. the genres didn't match :/")
            return

        return sorted(
            self.get_suggested_playlists(albums_by_genre),
            key=lambda album_group: len(album_group['albums']),
            reverse=True
        )

    def launch_playlist_picker(self):
        suggested_playlists = self.get_playlist_options()
        if len(suggested_playlists) == 0:
            self.ui.tell_user("Couldn't find any suggested playlists!")
            return
        def playlist_pick_handler(playlist):
            return self.playlist_creator.create_playlist_from_albums(
                playlist, self.get_num_tracks_per_album)
        InteractiveOptionPicker(
            suggested_playlists,
            playlist_pick_handler,
            self.ui,
            self._get_playlist_description,
        ).launch_interactive_picker()

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
            "a": self._get_create_playlist_from_an_artists_discography_callback(),
            "b": self._get_create_playlist_based_on_existing_playlist_callback(),
            "c": self.run_create_or_update_target_from_seed,
            "d": self.launch_playlist_picker,
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
        ).launch_interactive_picker()

    def _get_artist_from_user(self):
        artist_name = self.ui.get_non_empty_string("What artist interests you?")
        matching_artists = self.music_api_client.get_matching_artists(artist_name)
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
                lambda: self.get_playlist_from_user(
                    self.my_music_lib.get_playlist_by_name),
                get_new_playlist_name,
                get_num_tracks_per_album,
            )
        return callback

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