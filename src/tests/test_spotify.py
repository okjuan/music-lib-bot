from os import putenv
import unittest

from tests.fixtures import mock_artist, mock_track, mock_playlist, mock_audio_features
from packages.music_api_clients.models.album import Album
from packages.music_api_clients.models.artist import Artist
from packages.music_api_clients.spotify import Spotify


class TestSpotify(unittest.TestCase):
    def setUp(self):
        #putenv("SPOTIPY_CLIENT_ID", "x")
        #putenv("SPOTIPY_CLIENT_SECRET", "x")
        #putenv("SPOTIPY_REDIRECT_URI", "x")
        self.spotify = Spotify()

    def test_add_tracks(self):
        pass

    def test_get_artist_genres(self):
        artist = mock_artist(spotify_id="3nFkdlSjzX9mRTtwJOzDYB") # Jay-Z

        artist_genres = self.spotify.get_artist_genres(artist)

        self.assertEqual(
            sorted(['east coast hip hop', 'hip hop', 'rap']),
            sorted(artist_genres),
        )

    def test_get_my_albums(self):
        num_albums_to_fetch = 10

        albums = self.spotify.get_my_albums(num_albums_to_fetch)

        self.assertEqual(num_albums_to_fetch, len(albums))
        self.assertEqual(Album, type(albums[0]))
        self.assertEqual(Artist, type(albums[0].artists[0]))

    def test_get_artist_albums(self):
        artist = mock_artist(spotify_id="74ASZWbe4lXaubB36ztrGX") # Bob Dylan

        albums = self.spotify.get_artist_albums(artist)

        self.assertIn("Rough and Rowdy Ways", [album.name for album in albums])

    def test__get_playlist_tracks(self):
        playlist_id = "04Ajor0wgmBWSGKRLyR4nw" # playlist 'test__get_playlist_tracks'

        tracks = self.spotify._get_playlist_tracks(playlist_id)

        self.assertIn("Fast Fuse", [track.name for track in tracks])
        self.assertLess(100, len(tracks))

    def test_find_current_user_playlist(self):
        playlist_name = "Test Playlist: test_find_current_user_playlist"

        playlist_id = self.spotify.find_current_user_playlist(
            playlist_name)

        self.assertEqual("62y1x73aOCl7F52EcAfHbP", playlist_id)

    def test_populate_track_audio_features(self):
        track = mock_track(
            spotify_id="1ZZMu5cxiU4eFUNVwMnCJq", audio_features=None)

        self.spotify.set_track_audio_features([track])

        self.assertIsNotNone(track.audio_features)

    @unittest.skip("takes too long to run")
    def test_find_current_user_matching_playlists(self):
        playlists = self.spotify.find_current_user_matching_playlists(
            "test playlist for music.lib.bot")

        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0].name, "test playlist for music.lib.bot")
        self.assertEqual(playlists[0].spotify_id, "0n7rtEEIWS0SZuZLCjxjhN")

    @unittest.skip("takes too long to run")
    def test_find_current_user_matching_playlists(self):
        playlists = self.spotify.find_current_user_matching_playlists(
            "multiple test playlists for music.lib.bot")

        self.assertEqual(len(playlists), 2)
        self.assertIn(
            playlists[0].name,
            [
                "multiple test playlists for music.lib.bot v1",
                "multiple test playlists for music.lib.bot v2",
            ]
        )
        self.assertIn(
            playlists[0].spotify_id,
            [
                "0d8y7RfDpXDYH1jmzgF5Ii",
                "4LDXQjT9E9PbB9Tn8C5Yxk",
            ]
        )