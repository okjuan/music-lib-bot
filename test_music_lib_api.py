import unittest
from unittest.mock import patch, Mock, MagicMock

from fixtures import mock_album, mock_track, mock_artist
from music_lib_api import MusicLibApi


class TestMusicLibApi(unittest.TestCase):
    def setUp(self):
        self.music_lib_api = MusicLibApi()

    @unittest.skip("needs to be updated")
    @patch("music_lib_api.as_readable_key", return_value="unbelievable-funk")
    def test_group_albums_by_genre__single_album(self, _):
        albums_by_genre = self.music_lib_api.group_albums_by_genre([mock_album(name="jiggery pokery")])

        self.assertEqual(1, len(albums_by_genre.keys()), "Expected 1 group of albums")
        self.assertIn("unbelievable-funk", albums_by_genre)
        self.assertEqual(1, len(albums_by_genre["unbelievable-funk"]))
        self.assertEqual(
            "jiggery pokery",
            albums_by_genre["unbelievable-funk"][0]["name"],
        )

    @unittest.skip("needs to be updated")
    @patch("music_lib_api.as_readable_key", return_value="unbelievable-funk")
    def test_group_albums_by_genre__same_genre_key__groups_together(self, _):
        albums = [mock_album(name="jiggery pokery"), mock_album(name="mischief")]

        albums_by_genre = self.music_lib_api.group_albums_by_genre(albums)

        self.assertEqual(["unbelievable-funk"], list(albums_by_genre.keys()))
        self.assertEqual(2, len(albums_by_genre["unbelievable-funk"]))
        album_names = [a['name'] for a in albums_by_genre["unbelievable-funk"]]
        self.assertIn("jiggery pokery", album_names)
        self.assertIn("mischief", album_names)

    @unittest.skip("needs to be updated")
    @patch("music_lib_api.as_readable_key", side_effect=["unbelievable-funk", "ambient-whispering"])
    def test_group_albums_by_genre__diff_genre_key__groups_separately(self, _):
        albums = [mock_album(name="jiggery pokery"), mock_album(name="mischief")]

        albums_by_genre = self.music_lib_api.group_albums_by_genre(albums)

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

    def test_as_readable_key__multiple_genres__orders_alphabetically(self):
        genres = ['rock', 'jazz', 'pop']

        genre_string = self.music_lib_api.as_readable_key(genres)

        self.assertEqual("jazz, pop, rock", genre_string)

    def test_as_readable_key__single__returns(self):
        genres = ['rock']

        genre_string = self.music_lib_api.as_readable_key(genres)

        self.assertEqual("rock", genre_string)

    def test_as_readable_key__empty__defaults(self):
        genres = []

        genre_string = self.music_lib_api.as_readable_key(genres)

        self.assertEqual("unknown", genre_string)

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

        matches = self.music_lib_api.detect_genre_matches(albums_by_id)

        self.assertEqual(0, len(matches.keys()))

    def test_detect_genre_matches__two_albums__match_counts_are_symmetrical(self):
        albums_by_id = {
            "123": mock_album(id="123", genres=["A", "B", "C"]),
            "456": mock_album(id="456", genres=["A", "B", "D"]),
        }

        matches = self.music_lib_api.detect_genre_matches(albums_by_id)

        self.assertEqual(2, len(matches.keys()))
        self.assertIn("123", matches)
        self.assertIn("456", matches)
        self.assertEqual(1, len(matches["123"]))
        self.assertEqual(1, len(matches["456"]))
        self.assertEqual(2, len(matches["123"]["456"]))
        self.assertEqual(2, len(matches["456"]["123"]))
        self.assertEqual(["A", "B"], matches["123"]["456"])
        self.assertEqual(["A", "B"], matches["456"]["123"])

    def test_detect_genre_matches__no_matches__empty(self):
        albums_by_id = {
            "123": mock_album(id="123", genres=["A"]),
            "456": mock_album(id="456", genres=["B"]),
        }

        matches = self.music_lib_api.detect_genre_matches(albums_by_id)

        self.assertEqual(0, len(matches.keys()))

    def test_detect_genre_matches__some_matches__only_returns_entries_for_albums_w_matches(self):
        albums_by_id = {
            "123": mock_album(id="123", genres=["A"]),
            "456": mock_album(id="456", genres=["A"]),
            "789": mock_album(id="789", genres=["B"]),
        }

        matches = self.music_lib_api.detect_genre_matches(albums_by_id)

        self.assertEqual(2, len(matches.keys()))
        self.assertIn("123", matches)
        self.assertIn("456", matches)

    def test_detect_genre_matches__transitive_match__ignored(self):
        albums_by_id = {
            "123": mock_album(id="123", genres=["A", "B"]),
            "456": mock_album(id="456", genres=["B", "C"]),
            "789": mock_album(id="789", genres=["C", "D"]),
        }

        matches = self.music_lib_api.detect_genre_matches(albums_by_id)

        self.assertEqual(3, len(matches.keys()))
        self.assertIn("123", matches)
        self.assertIn("456", matches)
        self.assertIn("789", matches)
        self.assertEqual(1, len(matches["123"]))
        self.assertEqual(2, len(matches["456"]))
        self.assertEqual(1, len(matches["789"]))
        self.assertEqual(1, len(matches["123"]["456"]))
        self.assertEqual(1, len(matches["456"]["123"]))
        self.assertEqual(1, len(matches["456"]["789"]))
        self.assertEqual(1, len(matches["789"]["456"]))
        self.assertEqual(["B"], matches["123"]["456"])
        self.assertEqual(["B"], matches["456"]["123"])
        self.assertEqual(["C"], matches["456"]["789"])
        self.assertEqual(["C"], matches["789"]["456"])

    def test_group_albums__single_album__single_group(self):
        album_ids, matches = ["1"], {}

        album_groups = self.music_lib_api.group_albums(album_ids, matches)

        self.assertEqual(1, len(album_groups))

    def test_group_albums__single_qualifying_match__single_group(self):
        self.music_lib_api.MIN_MATCHES_TO_GROUP = 1

        album_ids, matches = ["1", "2"], {"1": {"2": ["jazz"]}, "2": {"1": ["jazz"]}}

        album_groups = self.music_lib_api.group_albums(album_ids, matches)

        self.assertEqual(1, len(album_groups))

    def test_group_albums__single_match__group_together(self):
        self.music_lib_api.MIN_MATCHES_TO_GROUP = 2

        album_ids, matches = ["1", "2"], {"1": {"2": ["jazz"]}, "2": {"1": ["jazz"]}}

        album_groups = self.music_lib_api.group_albums(album_ids, matches)

        self.assertEqual(1, len(album_groups))
        self.assertIn("jazz", album_groups)
        self.assertEqual(2, len(album_groups["jazz"]))

    def test_group_albums__transitive_match__does_not_group(self):
        self.music_lib_api.MIN_MATCHES_TO_GROUP = 1
        album_ids = ["2", "1", "3"]
        matches = {
            "1": {"2": ["jazz"]},
            "2": {"1": ["jazz"], "3": ["rock"]},
            "3": {"2": ["rock"]}
        }

        album_groups = self.music_lib_api.group_albums(album_ids, matches)

        self.assertEqual(2, len(album_groups))

    def test_group_albums__disjoint_matches__includes_all_group_variations(self):
        self.music_lib_api.MIN_MATCHES_TO_GROUP = 1
        album_ids = ["2", "1", "3", "4"]
        matches = {
            "1": {"2": ["jazz"]},
            "2": {"1": ["jazz"], "3": ["rock"], "4": ["pop"]},
            "3": {"2": ["rock"]},
            "4": {"2": ["pop"]}
        }

        album_groups = self.music_lib_api.group_albums(album_ids, matches)

        self.assertEqual(3, len(album_groups))

    @unittest.skip("Integration tests disabled by default")
    def test_fetch_albums__few(self):
        album_to_fetch = 10

        albums = self.music_lib_api.fetch_albums(album_to_fetch)

        self.assertEqual(10, len(albums))

    @unittest.skip("Integration tests disabled by default")
    def test_fetch_albums__many(self):
        album_to_fetch = 101

        albums = self.music_lib_api.fetch_albums(album_to_fetch)

        self.assertEqual(101, len(albums))

    @unittest.skip("Integration tests disabled by default")
    def test_fetch_albums__more_than_possible__returns_max(self):
        album_to_fetch = 1000

        albums = self.music_lib_api.fetch_albums(album_to_fetch)

        self.assertGreater(1000, len(albums))
        self.assertLess(0, len(albums))


def get_num_times_called(mock):
    if isinstance(mock, Mock):
        return len(mock.call_args_list)
    return NotImplemented

if __name__ == '__main__':
    unittest.main()