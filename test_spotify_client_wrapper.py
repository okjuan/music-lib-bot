import unittest

from os import putenv
from spotify_client_wrapper import SpotifyClientWrapper


class TestSpotifyClientWrapper(unittest.TestCase):
    def setUp(self):
        #putenv("SPOTIPY_CLIENT_ID", "x")
        #putenv("SPOTIPY_CLIENT_SECRET", "x")
        #putenv("SPOTIPY_REDIRECT_URI", "x")
        self.spotify_client_wrapper = SpotifyClientWrapper()

    def test_add_tracks(self):
        pass

    @unittest.skip("FIXME; and, in any case, Integration tests disabled by default")
    def test_fetch_albums__few(self):
        album_to_fetch = 10

        albums = self.spotify_client_wrapper.get_my_albums(album_to_fetch)

        self.assertEqual(10, len(albums))

    @unittest.skip("FIXME; and, in any case, Integration tests disabled by default")
    def test_fetch_albums__many(self):
        album_to_fetch = 101

        albums = self.spotify_client_wrapper.get_my_albums(album_to_fetch)

        self.assertEqual(101, len(albums))

    @unittest.skip("FIXME; and, in any case, Integration tests disabled by default")
    def test_fetch_albums__more_than_possible__returns_max(self):
        album_to_fetch = 1000

        albums = self.spotify_client_wrapper.get_my_albums(album_to_fetch)

        self.assertGreater(1000, len(albums))
        self.assertLess(0, len(albums))