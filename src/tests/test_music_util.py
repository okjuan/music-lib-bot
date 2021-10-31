import unittest
from unittest.mock import patch, MagicMock

from tests.fixtures import mock_album, mock_artist, mock_artist_dict
from app.lib.music_util import MusicUtil


class TestMusicUtil(unittest.TestCase):
    def setUp(self):
        self.music_util = MusicUtil(MagicMock())

    def test_is_a_demo__basic_scenario__matches(self):
        album = mock_album(name="The Witmark Demos: 1962-1964 (The Bootleg Series Vol. 9)")

        is_demo = self.music_util.is_a_demo(album)

        self.assertTrue(is_demo)

    def test_is_a_demo__ignores_partial_word_match(self):
        album = mock_album(name="Sin Miedo (del Amory Otros Demonios) ∞ [Deluxe Version]")

        is_demo = self.music_util.is_a_demo(album)

        self.assertFalse(is_demo)

    def test_is_a_bootleg__basic_scenario__matches(self):
        album = mock_album(name="The Bootleg Series Volumes 1-3 (Rare and Unreleased) 1961-1991")

        is_bootleg = self.music_util.is_a_bootleg(album)

        self.assertTrue(is_bootleg)

    def test_is_a_bootleg__ignores_partial_word_match(self):
        album = mock_album(name="Bootlegging the Bootleggers")

        is_bootleg = self.music_util.is_a_bootleg(album)

        self.assertFalse(is_bootleg)

    def test_is_live__in_parentheses__matches(self):
        album = mock_album(name="An Evening With Herbie Hancock & Chick Corea In Concert (Live)")

        is_live = self.music_util.is_live(album)

        self.assertTrue(is_live)

    def test_is_live__in_brackets__matches(self):
        album = mock_album(
            name="Miles in Montreux (feat. Rich Margitza, Adam Holzman, Benny Rietveld) [Live]")

        is_live = self.music_util.is_live(album)

        self.assertTrue(is_live)

    def test_is_live__ignores_word_in_title(self):
        # Example 1
        album = mock_album(name="LONG.LIVE.A$AP")

        is_live = self.music_util.is_live(album)

        self.assertFalse(is_live)

        # Example 2
        album = mock_album(name="Live Through This")

        is_live = self.music_util.is_live(album)

        self.assertFalse(is_live)

    def test__strip_metadata_in_parentheses_or_brackets__removes(self):
        # Example 1
        album_name = "Collectors' Items (RVG Remaster)"

        stripped_album_name = self.music_util._strip_metadata_in_parentheses_or_brackets(
            album_name)

        self.assertEqual("Collectors' Items", stripped_album_name)

        # Example 2
        album_name = "Collectors' Items [RVG Remaster]"

        stripped_album_name = self.music_util._strip_metadata_in_parentheses_or_brackets(
            album_name)

        self.assertEqual("Collectors' Items", stripped_album_name)

    def test_filter_out_duplicates__capitalization(self):
        albums = [
            mock_album(name="Porgy and Bess"),
            mock_album(name="Porgy And Bess")
        ]
        choose_arbitrary_album = lambda album1, album2: album1

        albums = self.music_util.filter_out_duplicates(albums, choose_arbitrary_album)

        self.assertEqual(1, len(albums))

    def test_get_most_popular_artist__empty(self):
        artists = []

        most_popular_artist = self.music_util.get_most_popular_artist(artists)

        self.assertIsNone(most_popular_artist)

    def test_get_most_popular_artist__single_artist(self):
        artists = [mock_artist(name="jimmy reed")]

        most_popular_artist = self.music_util.get_most_popular_artist(artists)

        self.assertEqual("jimmy reed", most_popular_artist.name)

    def test_get_most_popular_artist__multiple_artists(self):
        artists = [
            mock_artist(name="jimmy reed", popularity=1),
            mock_artist(name="howlin' wolf", popularity=3),
            mock_artist(name="junior wells", popularity=2),
        ]

        most_popular_artist = self.music_util.get_most_popular_artist(artists)

        self.assertEqual("howlin' wolf", most_popular_artist.name)
        self.assertEqual(3, most_popular_artist.popularity)

    def test_get_albums_as_readable_list__empty(self):
        albums = []

        albums_as_readable_str = self.music_util.get_albums_as_readable_list(albums)

        self.assertEqual("", albums_as_readable_str)

    def test_get_albums_as_readable_list__one_album(self):
        artist = mock_artist_dict(name="mock artist")
        album = mock_album(artists=[artist], name="mock album")
        albums = [album]

        albums_as_readable_str = self.music_util.get_albums_as_readable_list(albums)

        self.assertEqual("- mock album by mock artist", albums_as_readable_str)

    def test_get_albums_as_readable_list__multiple_artists(self):
        artist1, artist2 = mock_artist_dict(name="mock artist 1"), mock_artist_dict(name="mock artist 2")
        album = mock_album(artists=[artist1, artist2], name="mock album")
        albums = [album]

        albums_as_readable_str = self.music_util.get_albums_as_readable_list(albums)

        self.assertEqual("- mock album by mock artist 1, mock artist 2", albums_as_readable_str)

    def test_get_albums_as_readable_list__multiple_albums(self):
        artist = mock_artist_dict(name="mock artist")
        album1 = mock_album(artists=[artist], name="mock album 1")
        album2 = mock_album(artists=[artist], name="mock album 2")
        albums = [album1, album2]

        albums_as_readable_str = self.music_util.get_albums_as_readable_list(albums)

        self.assertEqual("- mock album 1 by mock artist\n- mock album 2 by mock artist", albums_as_readable_str)

    def test_as_readable_key__multiple_genres__orders_alphabetically(self):
        genres = ['rock', 'jazz', 'pop']

        genre_string = self.music_util._as_readable_key(genres)

        self.assertEqual("jazz, pop, rock", genre_string)

    def test_as_readable_key__single__returns(self):
        genres = ['rock']

        genre_string = self.music_util._as_readable_key(genres)

        self.assertEqual("rock", genre_string)

    def test_as_readable_key__empty__defaults(self):
        genres = []

        genre_string = self.music_util._as_readable_key(genres)

        self.assertEqual("unknown", genre_string)

    def test__detect_genre_matches__no_matches(self):
        mock_albums = {
            'id1': mock_album(id='id1', genres=['hip hop']),
            'id2': mock_album(id='id2', genres=['rock'])
        }

        albums_by_genre = self.music_util._detect_genre_matches(mock_albums)

        self.assertEqual(0, len(albums_by_genre.keys()))

    def test__detect_genre_matches__2_albums_1_genre(self):
        mock_albums = {
            'id1': mock_album(id='id1', genres=['hip hop']),
            'id2': mock_album(id='id2', genres=['hip hop'])
        }

        genre_matches = self.music_util._detect_genre_matches(mock_albums)

        self.assertEqual(sorted(['id1', 'id2']), sorted(list(genre_matches.keys())))
        self.assertEqual(['id2'], list(genre_matches['id1'].keys()))
        self.assertEqual(['id1'], list(genre_matches['id2'].keys()))
        self.assertEqual(['hip hop'], list(genre_matches['id1']['id2']))
        self.assertEqual(['hip hop'], list(genre_matches['id2']['id1']))

    def test__detect_genre_matches__3_albums_1_genre(self):
        mock_albums = {
            'id1': mock_album(id='id1', genres=['hip hop']),
            'id2': mock_album(id='id2', genres=['hip hop']),
            'id3': mock_album(id='id3', genres=['hip hop']),
        }

        genre_matches = self.music_util._detect_genre_matches(mock_albums)

        self.assertEqual(sorted(['id1', 'id2', 'id3']), sorted(list(genre_matches.keys())))
        self.assertEqual(sorted(['id2', 'id3']), sorted(list(genre_matches['id1'].keys())))
        self.assertEqual(sorted(['id1', 'id3']), sorted(list(genre_matches['id2'].keys())))
        self.assertEqual(sorted(['id1', 'id2']), sorted(list(genre_matches['id3'].keys())))
        self.assertEqual(sorted(['hip hop']), sorted(list(genre_matches['id1']['id2'])))
        self.assertEqual(sorted(['hip hop']), sorted(list(genre_matches['id1']['id3'])))
        self.assertEqual(sorted(['hip hop']), sorted(list(genre_matches['id2']['id1'])))
        self.assertEqual(sorted(['hip hop']), sorted(list(genre_matches['id2']['id3'])))
        self.assertEqual(sorted(['hip hop']), sorted(list(genre_matches['id3']['id1'])))
        self.assertEqual(sorted(['hip hop']), sorted(list(genre_matches['id3']['id2'])))

    def test__detect_genre_matches__2_albums_2_genres(self):
        mock_albums = {
            'id1': mock_album(id='id1', genres=['hip hop', 'rap']),
            'id2': mock_album(id='id2', genres=['hip hop', 'rap'])
        }

        genre_matches = self.music_util._detect_genre_matches(mock_albums)

        self.assertEqual(sorted(['id1', 'id2']), sorted(list(genre_matches.keys())))
        self.assertEqual(['id2'], list(genre_matches['id1'].keys()))
        self.assertEqual(['id1'], list(genre_matches['id2'].keys()))
        self.assertEqual(sorted(['hip hop', 'rap']), sorted(list(genre_matches['id1']['id2'])))

    def test__detect_genre_matches__3_albums_3_genres(self):
        mock_albums = {
            'id1': mock_album(id='id1', genres=['hip hop', 'rap', 'trap']),
            'id2': mock_album(id='id2', genres=['hip hop', 'rap', 'trap']),
            'id3': mock_album(id='id3', genres=['hip hop', 'rap', 'trap'])
        }

        genre_matches = self.music_util._detect_genre_matches(mock_albums)

        self.assertEqual(sorted(['id1', 'id2', 'id3']), sorted(list(genre_matches.keys())))
        self.assertEqual(sorted(['id2', 'id3']), sorted(list(genre_matches['id1'].keys())))
        self.assertEqual(sorted(['id1', 'id3']), sorted(list(genre_matches['id2'].keys())))
        self.assertEqual(sorted(['id1', 'id2']), sorted(list(genre_matches['id3'].keys())))
        self.assertEqual(sorted(['hip hop', 'rap', 'trap']), sorted(list(genre_matches['id1']['id2'])))
        self.assertEqual(sorted(['hip hop', 'rap', 'trap']), sorted(list(genre_matches['id1']['id3'])))
        self.assertEqual(sorted(['hip hop', 'rap', 'trap']), sorted(list(genre_matches['id2']['id1'])))
        self.assertEqual(sorted(['hip hop', 'rap', 'trap']), sorted(list(genre_matches['id2']['id3'])))
        self.assertEqual(sorted(['hip hop', 'rap', 'trap']), sorted(list(genre_matches['id3']['id1'])))
        self.assertEqual(sorted(['hip hop', 'rap', 'trap']), sorted(list(genre_matches['id3']['id2'])))

    def test__group_albums__2_albums_1_genre(self):
        album_ids= ['id1', 'id2']
        genre_matches = {
            'id1': {
                'id2': ['rap']
            },
            'id2': {
                'id1': ['rap']
            },
        }

        album_groups = self.music_util._group_albums(album_ids, genre_matches)

        self.assertEqual([{
                'album ids': {'id1', 'id2'},
                'genres': ['rap']
            }], album_groups)

    def test__group_albums__2_albums_2_genre(self):
        album_ids= ['id1', 'id2']
        genre_matches = {
            'id1': {
                'id2': ['rap', 'hip hop']
            },
            'id2': {
                'id1': ['rap', 'hip hop']
            },
        }

        album_groups = self.music_util._group_albums(album_ids, genre_matches)

        self.assertEqual(1, len(album_groups))
        self.assertEqual({'id1', 'id2'}, album_groups[0]['album ids'])
        self.assertEqual(sorted(['rap', 'hip hop']), sorted(album_groups[0]['genres']))

    @unittest.skip("needs to be fixed")
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

    @unittest.skip("needs to be fixed")
    @patch("music_lib_api.as_readable_key", return_value="unbelievable-funk")
    def test_group_albums_by_genre__same_genre_key__groups_together(self, _):
        albums = [mock_album(name="jiggery pokery"), mock_album(name="mischief")]

        albums_by_genre = self.music_lib_api.group_albums_by_genre(albums)

        self.assertEqual(["unbelievable-funk"], list(albums_by_genre.keys()))
        self.assertEqual(2, len(albums_by_genre["unbelievable-funk"]))
        album_names = [a['name'] for a in albums_by_genre["unbelievable-funk"]]
        self.assertIn("jiggery pokery", album_names)
        self.assertIn("mischief", album_names)

    @unittest.skip("needs to be fixed")
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

    @unittest.skip("ported from old test")
    def test__group_albums_by_genre(self):
        albums_by_id = {
            "123": mock_album(id="123", genres=['jazz']),
            "456": mock_album(id="456", genres=['jazz']),
        }

        album_groups = _group_albums(albums_by_id)

        self.assertEqual(1, len(album_groups))
        self.assertEqual(2, len(album_groups[0]))
        album_ids = [album.id for album in album_groups[0]]
        self.assertIn("123", album_ids)
        self.assertIn("456", album_ids)

    @unittest.skip("ported from old test")
    def test_detect_genre_matches__single_album__empty(self):
        albums_by_id = {"123": mock_album()}

        matches = self.music_lib_api.detect_genre_matches(albums_by_id)

        self.assertEqual(0, len(matches.keys()))

    @unittest.skip("ported from old test")
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

    @unittest.skip("ported from old test")
    def test_detect_genre_matches__no_matches__empty(self):
        albums_by_id = {
            "123": mock_album(id="123", genres=["A"]),
            "456": mock_album(id="456", genres=["B"]),
        }

        matches = self.music_lib_api.detect_genre_matches(albums_by_id)

        self.assertEqual(0, len(matches.keys()))

    @unittest.skip("ported from old test")
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

    @unittest.skip("ported from old test")
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

    @unittest.skip("ported from old test")
    def test_group_albums__single_album__single_group(self):
        album_ids, matches = ["1"], {}

        album_groups = self.music_lib_api.group_albums(album_ids, matches)

        self.assertEqual(1, len(album_groups))

    @unittest.skip("ported from old test")
    def test_group_albums__single_qualifying_match__single_group(self):
        self.music_lib_api.MIN_MATCHES_TO_GROUP = 1

        album_ids, matches = ["1", "2"], {"1": {"2": ["jazz"]}, "2": {"1": ["jazz"]}}

        album_groups = self.music_lib_api.group_albums(album_ids, matches)

        self.assertEqual(1, len(album_groups))

    @unittest.skip("ported from old test")
    def test_group_albums__single_match__group_together(self):
        self.music_lib_api.MIN_MATCHES_TO_GROUP = 2

        album_ids, matches = ["1", "2"], {"1": {"2": ["jazz"]}, "2": {"1": ["jazz"]}}

        album_groups = self.music_lib_api.group_albums(album_ids, matches)

        self.assertEqual(1, len(album_groups))
        self.assertIn("jazz", album_groups)
        self.assertEqual(2, len(album_groups["jazz"]))

    @unittest.skip("ported from old test")
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

    @unittest.skip("ported from old test")
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


if __name__ == '__main__':
    unittest.main()