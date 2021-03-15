import unittest
from unittest.mock import patch, Mock, MagicMock

from fixtures import mock_album, mock_track, mock_artist
from music_lib_bot import (
    add_albums_to_playlist,
    group_albums_by_genre,
    get_genre_key_string,
    detect_genre_matches,
    group_albums,
)


class TestMusicLibBot(unittest.TestCase):
    def test_add_albums_to_playlist__empty(self):
        add_albums_to_playlist([])

    @unittest.skip("needs to be updated")
    @patch("music_lib_bot.create_playlist")
    @patch("music_lib_bot.get_most_popular_tracks", return_value=[mock_track()])
    def test_add_albums_to_playlist__multiple_albums(self, mock_get_most_popular_tracks, mock_create_playlist):
        albums = [mock_album(), mock_album(), mock_album()]

        add_albums_to_playlist(albums)

        self.assertEqual(1, get_num_times_called(mock_create_playlist))
        self.assertEqual(3, get_num_times_called(mock_get_most_popular_tracks))
        mock_create_playlist.assert_any_call(
            "created by music.lib.bot", [mock_track(), mock_track(), mock_track()])

    @unittest.skip("needs to be updated")
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

    @unittest.skip("needs to be updated")
    @patch("music_lib_bot.get_genre_key_string", return_value="unbelievable-funk")
    def test_group_albums_by_genre__same_genre_key__groups_together(self, _):
        albums = [mock_album(name="jiggery pokery"), mock_album(name="mischief")]

        albums_by_genre = group_albums_by_genre(albums)

        self.assertEqual(["unbelievable-funk"], list(albums_by_genre.keys()))
        self.assertEqual(2, len(albums_by_genre["unbelievable-funk"]))
        album_names = [a['name'] for a in albums_by_genre["unbelievable-funk"]]
        self.assertIn("jiggery pokery", album_names)
        self.assertIn("mischief", album_names)

    @unittest.skip("needs to be updated")
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

    def test_get_genre_key_string__multiple_genres__orders_alphabetically(self):
        genres = ['rock', 'jazz', 'pop']

        genre_string = get_genre_key_string(genres)

        self.assertEqual("jazz, pop, rock", genre_string)

    def test_get_genre_key_string__same_genre__groups_together(self):
        genres = ['rock']

        genre_string = get_genre_key_string(genres)

        self.assertEqual("rock", genre_string)

    def test_get_genre_key_string__no_genre__defaults(self):
        genres = []

        genre_string = get_genre_key_string(genres)

        self.assertEqual("unknown genre", genre_string)

    @unittest.skip("function no longer exists")
    def test__group_albums_by_genre(self):
        albums_by_id = {
            "123": mock_album(id="123", genres=['jazz']),
            "456": mock_album(id="456", genres=['jazz']),
        }

        album_groups = None # _group_albums_by_genre(albums_by_id)

        self.assertEqual(1, len(album_groups))
        self.assertEqual(2, len(album_groups[0]))
        album_ids = [album['id'] for album in album_groups[0]]
        self.assertIn("123", album_ids)
        self.assertIn("456", album_ids)

    def test_detect_genre_matches__single_album__empty(self):
        albums_by_id = {"123": mock_album()}

        matches = detect_genre_matches(albums_by_id)

        self.assertEqual(0, len(matches.keys()))

    def test_detect_genre_matches__two_albums__match_counts_are_symmetrical(self):
        albums_by_id = {
            "123": mock_album(id="123", genres=["A", "B", "C"]),
            "456": mock_album(id="456", genres=["A", "B", "D"]),
        }

        matches = detect_genre_matches(albums_by_id)

        self.assertEqual(2, len(matches.keys()))
        self.assertIn("123", matches)
        self.assertIn("456", matches)
        self.assertEqual(1, len(matches["123"]))
        self.assertEqual(1, len(matches["456"]))
        self.assertEqual(2, matches["123"]["456"])
        self.assertEqual(2, matches["456"]["123"])

    def test_detect_genre_matches__no_matches__empty(self):
        albums_by_id = {
            "123": mock_album(id="123", genres=["A"]),
            "456": mock_album(id="456", genres=["B"]),
        }

        matches = detect_genre_matches(albums_by_id)

        self.assertEqual(0, len(matches.keys()))

    def test_detect_genre_matches__some_matches__only_returns_entries_for_albums_w_matches(self):
        albums_by_id = {
            "123": mock_album(id="123", genres=["A"]),
            "456": mock_album(id="456", genres=["A"]),
            "789": mock_album(id="789", genres=["B"]),
        }

        matches = detect_genre_matches(albums_by_id)

        self.assertEqual(2, len(matches.keys()))
        self.assertIn("123", matches)
        self.assertIn("456", matches)

    def test_detect_genre_matches__transitive_match__ignored(self):
        albums_by_id = {
            "123": mock_album(id="123", genres=["A", "B"]),
            "456": mock_album(id="456", genres=["B", "C"]),
            "789": mock_album(id="789", genres=["C", "D"]),
        }

        matches = detect_genre_matches(albums_by_id)

        self.assertEqual(3, len(matches.keys()))
        self.assertIn("123", matches)
        self.assertIn("456", matches)
        self.assertIn("789", matches)
        self.assertEqual(1, len(matches["123"]))
        self.assertEqual(2, len(matches["456"]))
        self.assertEqual(1, len(matches["789"]))
        self.assertEqual(1, matches["123"]["456"])
        self.assertEqual(1, matches["456"]["123"])
        self.assertEqual(1, matches["456"]["789"])
        self.assertEqual(1, matches["789"]["456"])

    def test_group_albums(self):
        album_ids, matches = ["1"], {}

        album_groups = group_albums(album_ids, matches)

        self.assertEqual(1, len(album_groups))

    @patch("music_lib_bot.MIN_MATCHES_TO_GROUP", 1)
    def test_group_albums__single_qualifying_match__single_group(self):
        album_ids, matches = ["1", "2"], {"1": {"2": 1}, "2": {"1": 1}}

        album_groups = group_albums(album_ids, matches)

        self.assertEqual(1, len(album_groups))

    @patch("music_lib_bot.MIN_MATCHES_TO_GROUP", 2)
    def test_group_albums__single_nonqualifying_match__separate_groups(self):
        album_ids, matches = ["1", "2"], {"1": {"2": 1}, "2": {"1": 1}}

        album_groups = group_albums(album_ids, matches)

        self.assertEqual(2, len(album_groups))
        self.assertTrue(
            (album_groups[0] == ["1"] and album_groups[1] == ["2"])
            or (album_groups[1] == ["1"] and album_groups[0] == ["2"])
        )


def get_num_times_called(mock):
    if isinstance(mock, Mock):
        return len(mock.call_args_list)
    return NotImplemented

if __name__ == '__main__':
    unittest.main()