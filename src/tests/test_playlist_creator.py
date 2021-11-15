import unittest
from unittest.mock import MagicMock

from tests.fixtures import mock_album, mock_artist
from app.playlist_creator import PlaylistCreator


class TestPlaylistCreator(unittest.TestCase):
    def setUp(self):
        self.playlist_creator = PlaylistCreator(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock()
        )

    def test_get_num_diff_artists(self):
        albums = []

        num = self.playlist_creator.get_num_diff_artists(albums)

        self.assertEqual(0, num)

    def test_get_num_diff_artists__single__counts(self):
        albums = [mock_album(artists=[mock_artist()])]

        num = self.playlist_creator.get_num_diff_artists(albums)

        self.assertEqual(1, num)

    def test_get_num_diff_artists__duplicate__counts_once(self):
        albums = [
            mock_album(artists=[mock_artist(id="123")]),
            mock_album(artists=[mock_artist(id="123")]),
        ]

        num = self.playlist_creator.get_num_diff_artists(albums)

        self.assertEqual(1, num)

    def test_get_num_diff_artists__diff_ids__counts_both(self):
        albums = [
            mock_album(artists=[mock_artist(id="123")]),
            mock_album(artists=[mock_artist(id="456")]),
        ]

        num = self.playlist_creator.get_num_diff_artists(albums)

        self.assertEqual(2, num)


if __name__ == '__main__':
    unittest.main()