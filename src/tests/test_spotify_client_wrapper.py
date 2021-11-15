from os import putenv
import unittest

from app.models.album import Album
from app.lib.spotify_client_wrapper import SpotifyClientWrapper


class TestSpotifyClientWrapper(unittest.TestCase):
    def setUp(self):
        #putenv("SPOTIPY_CLIENT_ID", "x")
        #putenv("SPOTIPY_CLIENT_SECRET", "x")
        #putenv("SPOTIPY_REDIRECT_URI", "x")
        self.spotify_client_wrapper = SpotifyClientWrapper()

    def test_add_tracks(self):
        pass

    def test_get_my_albums(self):
        num_albums_to_fetch = 10

        albums = self.spotify_client_wrapper.get_my_albums(num_albums_to_fetch)

        self.assertEqual(num_albums_to_fetch, len(albums))
        self.assertEqual(Album, type(albums[0]))

    def test_get_artist_albums(self):
        artist_id = "74ASZWbe4lXaubB36ztrGX" # Bob Dylan

        albums = self.spotify_client_wrapper.get_artist_albums(artist_id)

        self.assertIn("Rough and Rowdy Ways", [album.name for album in albums])

    def test__get_playlist_tracks(self):
        playlist_id = "04Ajor0wgmBWSGKRLyR4nw" # playlist 'test__get_playlist_tracks'

        tracks = self.spotify_client_wrapper._get_playlist_tracks(playlist_id)

        self.assertIn("Fast Fuse", [track.name for track in tracks])
        self.assertLess(100, len(tracks))

    def test_find_current_user_playlist(self):
        playlist_name = "Test Playlist: test_find_current_user_playlist"

        playlist_id = self.spotify_client_wrapper.find_current_user_playlist(
            playlist_name)

        self.assertEqual("62y1x73aOCl7F52EcAfHbP", playlist_id)