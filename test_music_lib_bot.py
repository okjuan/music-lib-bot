import unittest
from unittest.mock import patch, Mock

from fixtures import mock_album, mock_track
from music_lib_bot import add_albums_to_playlist


class TestMusicLibBot(unittest.TestCase):
    def test_add_albums_to_playlist__empty(self):
        add_albums_to_playlist([])

    @patch("music_lib_bot.create_playlist")
    @patch("music_lib_bot.get_most_popular_tracks", return_value=[mock_track()])
    def test_add_albums_to_playlist__multiple_albums(self, mock_get_most_popular_tracks, mock_create_playlist):
        albums = [mock_album(), mock_album(), mock_album()]

        add_albums_to_playlist(albums)

        self.assertEqual(1, get_num_times_called(mock_create_playlist))
        self.assertEqual(3, get_num_times_called(mock_get_most_popular_tracks))
        mock_create_playlist.assert_any_call(
            "created by music.lib.bot", [mock_track(), mock_track(), mock_track()])


def get_num_times_called(mock):
    if isinstance(mock, Mock):
        return len(mock.call_args_list)
    return NotImplemented

if __name__ == '__main__':
    unittest.main()