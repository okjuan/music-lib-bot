import unittest
from unittest.mock import patch, Mock, MagicMock

from fixtures import mock_album, mock_track, mock_artist
from music_lib_bot import (
    add_albums_to_playlist,
    group_albums_by_genre,
    get_genre_key_string,
    _group_albums_by_genre
)


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

    @patch("music_lib_bot.get_genre_key_string", return_value="unbelievable-funk")
    def test_group_albums_by_genre__single_album(self, _):
        albums_by_genre = group_albums_by_genre([mock_album(name="jiggery pokery")])

        self.assertEqual(1, len(albums_by_genre.keys()), "Expected 1 group of albums")
        self.assertIn("unbelievable-funk", albums_by_genre)
        self.assertEqual(1, len(albums_by_genre["unbelievable-funk"]))
        self.assertEqual(
            "jiggery pokery",
            albums_by_genre["unbelievable-funk"][0]["name"],
        )

    @patch("music_lib_bot.get_genre_key_string", return_value="unbelievable-funk")
    def test_group_albums_by_genre__same_genre_key__groups_together(self, _):
        albums = [mock_album(name="jiggery pokery"), mock_album(name="mischief")]

        albums_by_genre = group_albums_by_genre(albums)

        self.assertEqual(["unbelievable-funk"], list(albums_by_genre.keys()))
        self.assertEqual(2, len(albums_by_genre["unbelievable-funk"]))
        album_names = [a['name'] for a in albums_by_genre["unbelievable-funk"]]
        self.assertIn("jiggery pokery", album_names)
        self.assertIn("mischief", album_names)

    @patch("music_lib_bot.get_genre_key_string", side_effect=["unbelievable-funk", "ambient-whispering"])
    def test_group_albums_by_genre__diff_genre_key__groups_separately(self, _):
        albums = [mock_album(name="jiggery pokery"), mock_album(name="mischief")]

        albums_by_genre = group_albums_by_genre(albums)

        self.assertEqual(
            2,
            len(albums_by_genre.keys()),
            "Expected two separate groups of albums"
        )
        self.assertIn("unbelievable-funk", albums_by_genre)
        self.assertIn("ambient-whispering", albums_by_genre)
        self.assertEqual(1, len(albums_by_genre["unbelievable-funk"]))
        self.assertEqual(1, len(albums_by_genre["ambient-whispering"]))
        album_names = [a['name'] for a in albums_by_genre["unbelievable-funk"]]
        self.assertEqual("jiggery pokery", albums_by_genre["unbelievable-funk"][0]['name'])
        self.assertEqual("mischief", albums_by_genre["ambient-whispering"][0]['name'])

    @patch("music_lib_bot.spotify_client", return_value=Mock(artist=Mock(return_value=dict(genres=['rock', 'jazz', 'pop']))))
    def test_get_genre_key_string__multiple_genres__orders_alphabetically(self, _):
        genre_string = get_genre_key_string(mock_album(artists=[mock_artist()]))

        self.assertEqual("jazz---pop---rock", genre_string)

    @patch("music_lib_bot.spotify_client", return_value=Mock(artist=Mock(side_effect=[dict(genres=['rock'])])))
    def test_get_genre_key_string__same_genre__groups_together(self, _):
        genre_string = get_genre_key_string(mock_album(artists=[mock_artist()]))

        self.assertEqual("rock", genre_string)

    @patch("music_lib_bot.spotify_client", return_value=Mock(artist=Mock(side_effect=[dict(genres=[])])))
    def test_get_genre_key_string__no_genre__defaults(self, _):
        genre_string = get_genre_key_string(mock_album(artists=[mock_artist()]))

        self.assertEqual("unknown genre", genre_string)

    def test__group_albums_by_genre(self):
        albums = [mock_album(id="123", genres=['jazz']), mock_album(id="456", genres=['jazz'])]

        album_groups = _group_albums_by_genre(albums)

        self.assertEqual(1, len(album_groups))
        self.assertEqual(2, len(album_groups[0]))
        album_ids = [album['id'] for album in album_groups[0]]
        self.assertIn("123", album_ids)
        self.assertIn("456", album_ids)


def get_num_times_called(mock):
    if isinstance(mock, Mock):
        return len(mock.call_args_list)
    return NotImplemented

if __name__ == '__main__':
    unittest.main()