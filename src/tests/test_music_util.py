import unittest
from unittest.mock import patch, MagicMock

from tests.fixtures import mock_album, mock_artist, mock_playlist, mock_song_attribute_ranges, mock_track
from packages.music_management.music_util import MusicUtil


class TestMusicUtil(unittest.TestCase):
    def setUp(self):
        self.mock_spotify = MagicMock()
        self.music_util = MusicUtil(self.mock_spotify, MagicMock())

    def test_get_highly_common_genres__none_in_top_perecent__returns_genres_in_2nd_top_percent(self):
        mock_playlist_id = "mock-playlist-id"
        def mock_get_most_common_genres(_, top_percentage):
            if top_percentage == 10:
                return []
            elif top_percentage == 20:
                return ['rock']
            else:
                return []
        self.music_util.get_most_common_genres = mock_get_most_common_genres

        genres = self.music_util.get_highly_common_genres(mock_playlist_id)

        self.assertEqual(['rock'], genres)

    def test_get_highly_common_genres__no_genres(self):
        mock_playlist_id = "mock-playlist-id"
        def mock_get_most_common_genres(_, top_percentage):
            return []
        self.music_util.get_most_common_genres = mock_get_most_common_genres

        genres = self.music_util.get_highly_common_genres(mock_playlist_id)

        self.assertEqual([], genres)

    def test_get_most_common_genres__single_genre__returns_that_genre(self):
        playlist_id = "mock-playlist-id"
        top_percentage = 1
        self.music_util.get_genres_by_frequency = MagicMock(
            # rock constitutes 100%
            return_value=dict(rock=1))

        genres = self.music_util.get_most_common_genres(
            playlist_id, top_percentage)

        self.assertEqual(["rock"], genres)

    def test_get_most_common_genres__single_top_genre__returns_that_genre(self):
        playlist_id = "mock-playlist-id"
        top_percentage = 50
        self.music_util.get_genres_by_frequency = MagicMock(
            # rock constitutes 66%, pop %33%
            return_value=dict(rock=2, pop=1))

        genres = self.music_util.get_most_common_genres(
            playlist_id, top_percentage)

        self.assertEqual(["rock"], genres)

    def test_populate_popularity_if_absent__no_popularity__populates(self):
        tracks_without_popularity = [mock_track(popularity=None)]
        track_with_popularity = [mock_track(popularity=1)]
        self.mock_spotify.get_tracks = MagicMock(
            return_value=track_with_popularity)

        self.music_util.populate_popularity_if_absent(tracks_without_popularity)

        self.assertIsNotNone(tracks_without_popularity[0].popularity)
        self.assertEqual(1, tracks_without_popularity[0].popularity)

    def test_populate_popularity_if_absent__some_no_popularity__populates(self):
        input_tracks = [
            mock_track(uri="popularity=None", popularity=None),
            mock_track(uri="popularity is set", popularity=1)
        ]
        track_with_popularity = [
            mock_track(uri="popularity=None", popularity=2),
        ]
        self.mock_spotify.get_tracks = MagicMock(
            return_value=track_with_popularity)

        self.music_util.populate_popularity_if_absent(input_tracks)

        self.assertIsNotNone(input_tracks[0].popularity)
        self.assertEqual(2, len(input_tracks))
        self.assertEqual(2, input_tracks[0].popularity)
        self.assertEqual("popularity=None", input_tracks[0].uri)
        self.assertEqual(1, input_tracks[1].popularity)
        self.assertEqual("popularity is set", input_tracks[1].uri)

    def test_populate_popularity_if_absent__already_contains_popularity__no_change(self):
        input_tracks = [
            mock_track(uri="popularity is 2", popularity=2),
            mock_track(uri="popularity is 1", popularity=1)
        ]
        self.mock_spotify.get_tracks = MagicMock(
            return_value=[])

        self.music_util.populate_popularity_if_absent(input_tracks)

        self.assertIsNotNone(input_tracks[0].popularity)
        self.assertEqual(2, len(input_tracks))
        self.assertEqual(2, input_tracks[0].popularity)
        self.assertEqual("popularity is 2", input_tracks[0].uri)
        self.assertEqual(1, input_tracks[1].popularity)
        self.assertEqual("popularity is 1", input_tracks[1].uri)

    def test_populate_popularity_if_absent__some_no_popularity__only_fetches_data_for_those(self):
        input_tracks = [
            mock_track(uri="popularity=None", popularity=None),
            mock_track(uri="popularity is set", popularity=1),
            mock_track(uri="popularity=None #2", popularity=None),
        ]
        self.mock_spotify.get_tracks = MagicMock(
            return_value=[])

        self.music_util.populate_popularity_if_absent(input_tracks)

        self.mock_spotify.get_tracks.assert_called_once()
        self.mock_spotify.get_tracks.assert_called_once_with(
            ["popularity=None", "popularity=None #2"])

    def test_get_recommendations_based_on_tracks__groups_recommendations_with_same_percentage(self):
        track_ids = ["mock-track-id-1", "mock-track-id-10", "mock-track-id-2"]
        song_attribute_ranges = mock_song_attribute_ranges()
        mock_recommendations = {"mock-track-id-1": 1.0, "mock-track-id-10": 0.5, "mock-track-id-2": 0.5}
        self.music_util._get_recommendations_based_on_tracks_in_batches = MagicMock(
            return_value=mock_recommendations)

        recommendations_by_percent = self.music_util.get_recommendations_based_on_tracks(
            track_ids, song_attribute_ranges)

        self.assertEqual(2, len(recommendations_by_percent))
        self.assertIn(1.0, recommendations_by_percent)
        self.assertIn(0.5, recommendations_by_percent)
        self.assertEqual(
            ["mock-track-id-1"],
            recommendations_by_percent[1.0]
        )
        self.assertEqual(
            sorted(["mock-track-id-10", "mock-track-id-2"]),
            sorted(recommendations_by_percent[0.5])
        )

    def test__get_recommendations_based_on_tracks_in_batches__recommended_for_all_tracks__specifies_100_percent(self):
        track_ids, song_attribute_ranges = ["mock-seed-track"], mock_song_attribute_ranges()
        self.mock_spotify.get_recommendation_seed_limit = MagicMock(
            return_value=1)
        recommended_track = mock_track(id_="mock-recommendation")
        self.mock_spotify.get_recommendations_based_on_tracks = MagicMock(
            return_value=[recommended_track])

        recommendations_with_percentage = self.music_util._get_recommendations_based_on_tracks_in_batches(
            track_ids, song_attribute_ranges)

        self.assertEqual(1, len(recommendations_with_percentage))
        self.assertIn(recommended_track, recommendations_with_percentage)
        self.assertEqual(1.0, recommendations_with_percentage[recommended_track])

    def test__get_recommendations_based_on_tracks_in_batches__recommended_for_half_the_tracks__specifies_50_percent(self):
        track_ids = ["mock-seed-track-1", "mock-seed-track-2"]
        song_attribute_ranges = mock_song_attribute_ranges()
        self.mock_spotify.get_recommendation_seed_limit = MagicMock(
            return_value=1)
        recommended_track = mock_track(id_="mock-recommendation")
        def mock_get_recommendations(track_ids, _):
            if track_ids == ["mock-seed-track-1"]:
                return [recommended_track]
            elif track_ids == ["mock-seed-track-2"]:
                return []
            raise NotImplemented()
        self.mock_spotify.get_recommendations_based_on_tracks = MagicMock(
            side_effect=mock_get_recommendations)

        recommendations_with_percentage = self.music_util._get_recommendations_based_on_tracks_in_batches(
            track_ids, song_attribute_ranges)

        self.assertEqual(1, len(recommendations_with_percentage))
        self.assertIn(recommended_track, recommendations_with_percentage)
        self.assertEqual(0.5, recommendations_with_percentage[recommended_track])

    def test__get_recommendations_based_on_tracks_in_batches__multiple_percentages__recommends_all(self):
        track_ids = ["mock-seed-track-1", "mock-seed-track-2", "mock-seed-track-3"]
        song_attribute_ranges = mock_song_attribute_ranges()
        self.mock_spotify.get_recommendation_seed_limit = MagicMock(
            return_value=1)
        recommended_track1 = mock_track(id_="mock-recommendation-1")
        recommended_track2 = mock_track(id_="mock-recommendation-2")
        def mock_get_recommendations(track_ids, _):
            if track_ids == ["mock-seed-track-1"]:
                return [recommended_track1, recommended_track2]
            elif track_ids == ["mock-seed-track-2"]:
                return [recommended_track1]
            elif track_ids == ["mock-seed-track-3"]:
                return []
            raise NotImplemented()
        self.mock_spotify.get_recommendations_based_on_tracks = MagicMock(
            side_effect=mock_get_recommendations)

        recommendations_with_percentage = self.music_util._get_recommendations_based_on_tracks_in_batches(
            track_ids, song_attribute_ranges)

        self.mock_spotify.get_recommendations_based_on_tracks.assert_any_call(
            ["mock-seed-track-1"], song_attribute_ranges)
        self.mock_spotify.get_recommendations_based_on_tracks.assert_any_call(
            ["mock-seed-track-2"], song_attribute_ranges)
        self.mock_spotify.get_recommendations_based_on_tracks.assert_any_call(
            ["mock-seed-track-3"], song_attribute_ranges)
        self.assertEqual(2, len(recommendations_with_percentage))
        self.assertEqual(2.0/3.0, recommendations_with_percentage[recommended_track1])
        self.assertEqual(1.0/3.0, recommendations_with_percentage[recommended_track2])

    def test_get_artist_ids(self):
        mock_artists = [mock_artist(id="mock-id-123")]
        mock_tracks = [mock_track(artists=mock_artists)]
        self.mock_spotify.get_playlist = MagicMock(
            return_value=mock_playlist(tracks=mock_tracks))

        artist_ids = self.music_util.get_artist_ids("mock_playlist_id")

        self.assertEqual(["mock-id-123"], artist_ids)

    def test_get_genres_by_album_ids(self):
        album_ids = [
            "6YabPKtZAjxwyWbuO9p4ZD", # Highway 61 Revisited
            "2xG5VLMFnDKhjJhsiJDcGm", # I Walk The Line
        ]
        mock_albums = [
            mock_album(
                id="bob-dylan-album-id",
                artists=[mock_artist(id="bob-dylan-id")]
            ),
            mock_album(
                id="johnny-cash-album-id",
                artists=[mock_artist(id="johnny-cash-id")]
            ),
        ]
        self.mock_spotify.get_albums = MagicMock(
            return_value=mock_albums)
        def mock_get_artist_genres(artist_id):
            if artist_id == "bob-dylan-id":
                return ["folk rock"]
            elif artist_id == "johnny-cash-id":
                return ["country folk"]
            raise ValueError("unexpected artist ID")
        self.mock_spotify.get_artist_genres = MagicMock(
            side_effect=mock_get_artist_genres)

        genres_by_album_id = self.music_util.get_genres_by_album_ids(album_ids)

        self.assertEqual(["folk rock"], genres_by_album_id["bob-dylan-album-id"])
        self.assertEqual(["country folk"], genres_by_album_id["johnny-cash-album-id"])

    def test__add_artist_genres__single_album_single_genre(self):
        self.mock_spotify.get_artist_genres = MagicMock(return_value = ["jazz"])
        mock_albums = [mock_album(
            genres=[], artists=[mock_artist(id="mock-artist-id")], id="mock-album-id")]

        albums_with_genres = self.music_util._add_artist_genres(mock_albums)

        self.assertEqual(albums_with_genres["mock-album-id"].genres, ["jazz"])

    def test__add_artist_genres__multiple_albums_multiple_genres(self):
        mock_albums = [
            mock_album(
                genres=[],
                artists=[mock_artist(id="mock-artist-id-1")],
                id="mock-album-id-1"
            ),
            mock_album(
                genres=[],
                artists=[mock_artist(id="mock-artist-id-2")],
                id="mock-album-id-2"
            ),
        ]
        def mock_get_artist_genres(artist_id):
            if artist_id == "mock-artist-id-1":
                return ["jazz"]
            elif artist_id == "mock-artist-id-2":
                return ["rock", "prog rock"]
            raise ValueError("unexpected artist ID")
        self.mock_spotify.get_artist_genres = MagicMock(
            side_effect = mock_get_artist_genres)

        albums_with_genres = self.music_util._add_artist_genres(mock_albums)

        self.assertEqual(albums_with_genres["mock-album-id-1"].genres, ["jazz"])
        self.assertEqual(
            sorted(albums_with_genres["mock-album-id-2"].genres), ["prog rock", "rock"])

    def test_is_same_album_name__with_metadata_in_parentheses__returns_true(self):
        album, album_expand_edition = "The Prisoner", "The Prisoner (Expanded Edition)"

        is_same = self.music_util.is_same_album_name(album, album_expand_edition)

        self.assertTrue(is_same)

    def test_is_same_album_name__case_difference__returns_true(self):
        album, album_expand_edition = "the prisoner", "The Prisoner"

        is_same = self.music_util.is_same_album_name(album, album_expand_edition)

        self.assertTrue(is_same)

    def test_is_same_album_name__one_character_differs__returns_false(self):
        album, album_expand_edition = "The Prisoners", "The Prisoner"

        is_same = self.music_util.is_same_album_name(album, album_expand_edition)

        self.assertFalse(is_same)

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
        artist = mock_artist(name="mock artist")
        album = mock_album(artists=[artist], name="mock album")
        albums = [album]

        albums_as_readable_str = self.music_util.get_albums_as_readable_list(albums)

        self.assertEqual("- mock album by mock artist", albums_as_readable_str)

    def test_get_albums_as_readable_list__multiple_artists(self):
        artist1, artist2 = mock_artist(name="mock artist 1"), mock_artist(name="mock artist 2")
        album = mock_album(artists=[artist1, artist2], name="mock album")
        albums = [album]

        albums_as_readable_str = self.music_util.get_albums_as_readable_list(albums)

        self.assertEqual("- mock album by mock artist 1, mock artist 2", albums_as_readable_str)

    def test_get_albums_as_readable_list__multiple_albums(self):
        artist = mock_artist(name="mock artist")
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

    def test_filter_out_if_not_in_albums__all_tracks_in_albums__does_not_filter_any(self):
        mock_tracks = [mock_track(album=mock_album(id="album123"))]
        mock_albums = [mock_album(id="album123")]

        tracks = self.music_util.filter_out_if_not_in_albums(mock_tracks, mock_albums)

        self.assertEqual(tracks, mock_tracks)

    def test_filter_out_if_not_in_albums__some_tracks_in_albums__filter_out_others(self):
        mock_tracks = [
            mock_track(album=mock_album(id="album123")),
            mock_track(album=mock_album(id="some other album")),
        ]
        mock_albums = [mock_album(id="album123")]

        tracks = self.music_util.filter_out_if_not_in_albums(mock_tracks, mock_albums)

        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].album_id, "album123")

    def test_filter_out_if_not_in_albums__no_tracks__none_returned(self):
        mock_tracks = []
        mock_albums = [mock_album(id="album123")]

        tracks = self.music_util.filter_out_if_not_in_albums(mock_tracks, mock_albums)

        self.assertEqual(len(tracks), 0)

    def test_filter_out_if_not_in_albums__no_albums__none_returned(self):
        mock_tracks = [mock_track()]
        mock_albums = []

        tracks = self.music_util.filter_out_if_not_in_albums(mock_tracks, mock_albums)

        self.assertEqual(len(tracks), 0)

    def test_get_num_diff_artists(self):
        albums = []

        num = self.music_util.get_num_diff_artists(albums)

        self.assertEqual(0, num)

    def test_get_num_diff_artists__single__counts(self):
        albums = [mock_album(artists=[mock_artist()])]

        num = self.music_util.get_num_diff_artists(albums)

        self.assertEqual(1, num)

    def test_get_num_diff_artists__duplicate__counts_once(self):
        albums = [
            mock_album(artists=[mock_artist(id="123")]),
            mock_album(artists=[mock_artist(id="123")]),
        ]

        num = self.music_util.get_num_diff_artists(albums)

        self.assertEqual(1, num)

    def test_get_num_diff_artists__diff_ids__counts_both(self):
        albums = [
            mock_album(artists=[mock_artist(id="123")]),
            mock_album(artists=[mock_artist(id="456")]),
        ]

        num = self.music_util.get_num_diff_artists(albums)

        self.assertEqual(2, num)


if __name__ == '__main__':
    unittest.main()