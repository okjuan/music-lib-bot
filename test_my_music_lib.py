import unittest

from my_music_lib import MyMusicLib


class TestMyMusicLib(unittest.TestCase):
    def setUp(self):
        self.my_music_lib = MyMusicLib()

    def test_get_playlist(self):
        name = "Real Canadian Cheddar"

        playlist = self.my_music_lib.get_playlist(name)

        self.assertEqual(playlist['name'], "Real Canadian Cheddar")

    # Spotify Web API only allows fetching 50 playlists at a time
    # This is meant to test that a playlist is found even if not in first 50 to be fetched
    def test_get_playlist__not_in_initial_batch(self):
        name = "JPearson's Top of 2020"

        playlist = self.my_music_lib.get_playlist(name)

        self.assertEqual(playlist['name'], "JPearson's Top of 2020")

    def test_get_playlist__does_not_exist__returns_none(self):
        name = "This playlist does not exist"

        playlist = self.my_music_lib.get_playlist(name)

        self.assertIsNone(playlist)

    def test_get_my_albums_by_genres(self):
        genres = []

        my_albums = self.my_music_lib.get_my_albums_by_genres(genres)

        self.assertIsNone(my_albums)


if __name__ == '__main__':
    unittest.main()