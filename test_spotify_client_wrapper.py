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