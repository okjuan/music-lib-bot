# allows me to run:
# $ python app/music_lib_bot.py
import sys
sys.path.extend(['.', '../'])

from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.lib.playlist_creator import PlaylistCreator
from app.lib.playlist_stats import PlaylistStats
from app.lib.playlist_updater import PlaylistUpdater
from app.lib.interactive_option_picker import InteractiveOptionPicker
from app.lib.spotify_client_wrapper import SpotifyClientWrapper
from app.lib.ui import ConsoleUI

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
        self.playlist_stats = PlaylistStats(
            self.my_music_lib,
            self.music_util,
            self.ui.tell_user,
        )

    def run_add_tracks_from_my_saved_albums_with_similar_genres(self):
        playlist = self.get_playlist_from_user(
            self.my_music_lib.get_playlist_by_name)
        playlist_updater = PlaylistUpdater(
            playlist,
            self.my_music_lib,
            self.music_util,
            self.spotify_client,
            self.ui.tell_user,
            self.playlist_stats,
        )
        playlist_updater.add_tracks_from_my_saved_albums_with_similar_genres(
            self.get_num_tracks_per_album, self.get_num_albums_to_fetch)

    def run_add_recommended_tracks_with_similar_attributes(self):
        playlist = self.get_playlist_from_user(
            self.my_music_lib.get_playlist_with_track_audio_features)
        recommendation_criteria = self.music_util.get_playlist_recommendation_criteria_based_on_audio_attributes(
            playlist, self.playlist_stats)
        recommended_tracks = self.music_util.get_recommendations_based_on_tracks(
            [track.id for track in playlist.tracks],
            recommendation_criteria,
        )

        def recommended_track_pick_handler(track):
            self.my_music_lib.add_tracks_to_playlist(
                playlist.id, [track.id])
        def get_recommended_track_description(track):
            artist_names = [artist.name for artist in track.artists]
            return f"{track.name} by {', '.join(artist_names)}"
        InteractiveOptionPicker(
            recommended_tracks,
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

    def get_num_diff_artists(self, albums):
        return len({
            artist.id
            for album in albums
            for artist in album.artists
        })

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

    def get_playlist_options(self):
        albums_by_genre = self.get_albums_by_genre()
        if len(albums_by_genre) == 0:
            self.ui.tell_user("Couldn't match the albums into groups.. the genres didn't match :/")
            return

        return sorted(
            self.get_suggested_playlists(albums_by_genre),
            key=lambda album_group: len(album_group['albums']),
            reverse=True
        )

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
            "a": "Create playlist from an artist's discography",
            "b": "Create playlist from a playlist full of albums.",
            "c": "Create playlists from albums in your library that have matching genres.",
            "d": "To an existing playlist add tracks from my saved albums with similar genres",
            "e": "To an existing playlist add recommended tracks with similar attributes",
        }
        functions = {
            "a": self._get_create_playlist_from_an_artists_discography_callback(),
            "b": self._get_create_playlist_based_on_existing_playlist_callback(),
            "c": self.launch_playlist_picker,
            "d": self.run_add_tracks_from_my_saved_albums_with_similar_genres,
            "e": self.run_add_recommended_tracks_with_similar_attributes,
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

def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    ui = ConsoleUI()
    music_util = MusicUtil(spotify_client_wrapper, ui.tell_user)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util, ui.tell_user)
    MusicLibBot(spotify_client_wrapper, my_music_lib, music_util, ui).run()


if __name__ == "__main__":
    main()