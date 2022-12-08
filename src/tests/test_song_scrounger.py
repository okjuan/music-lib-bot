import unittest

from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch

from packages.song_scrounger.song_scrounger import SongScrounger
from tests.fixtures import mock_album, mock_artist, mock_track
from tests.helper import get_num_times_called


class TestSongScrounger(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_spotify_client = AsyncMock()
        self.song_scrounger = SongScrounger(self.mock_spotify_client)

    async def test_find_quoted_tokens__returns_single_token(self):
        text = "Should \"Find this\" at least"

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(tokens, ["Find this"], "Faild to find only token in text.")

    async def test_find_quoted_tokens(self):
        text = """
            When Don McLean recorded "American Pie" in 1972 he was remembering his own youth and the early innocence of rock 'n' roll fifteen years before; he may not have considered that he was also contributing the most sincere historical treatise ever fashioned on the vast social transition from the 1950s to the 1960s. For the record, "the day the music died" refers to Buddy Holly's February 1959 death in a plane crash in North Dakota that also took the lives of Richie ("La Bamba") Valens and The Big Bopper ("Chantilly Lace"). The rest of "American Pie" describes the major rock stars of the sixties and their publicity-saturated impact on the music scene: the Jester is Bob Dylan, the Sergeants are the Beatles, Satan is Mick Jagger. For 1950s teens who grew up with the phenomenon of primordial rock 'n' roll, the changes of the sixties might have seemed to turn the music into something very different: "We all got up to dance / Oh, but we never got the chance." There's no doubt that
        """

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(
            set(tokens),
            set(['American Pie', 'the day the music died', 'La Bamba', 'Chantilly Lace', 'American Pie', 'We all got up to dance / Oh, but we never got the chance.']),
            "Failed to find all tokens.",
        )

    async def test_find_quoted_tokens__no_tokens__returns_empty(self):
        text = "Nothing to see here."

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            [],
            "Should not have found any tokens.",
        )

    async def test_find_quoted_tokens__ignores_unbalanced(self):
        text = "For \" there is no closing quote"

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            [],
            "Should not have found any tokens."
        )

    async def test_find_quoted_tokens__ignores_final_unbalanced_quote(self):
        text = "Here's \"a token\" but for \" there is no closing quote"

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(tokens, ["a token"], "Should not have found any tokens.")

    async def test_find_quoted_tokens__preserves_order(self):
        text = "\"first token\" and \"second token\""

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(
            tokens[0],
            "first token",
            "Did not find first token in expected position."
        )
        self.assertEqual(
            tokens[1],
            "second token",
            "Did not find second token in expected position."
        )

    async def test_find_quoted_tokens__preserves_dups(self):
        text = "\"repeat token\" again \"repeat token\" again \"repeat token\""

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[0], "repeat token")
        self.assertEqual(tokens[1], "repeat token")
        self.assertEqual(tokens[2], "repeat token")

    async def test_find_names__strips_whitespace(self):
        text = MagicMock()
        self.song_scrounger.find_quoted_tokens = MagicMock(return_value = [
            "  leading",
            "trailing   ",
            "  both   ",
        ])

        song_names = self.song_scrounger.find_names(text)

        song_names_list = list(song_names)
        self.assertEqual(len(song_names_list), 3)
        self.assertEqual(set(song_names_list), set(["leading", "trailing", "both"]))

    async def test_find_names__strips_trailing_punctuation(self):
        text = MagicMock()
        self.song_scrounger.find_quoted_tokens = MagicMock(return_value = [
            ",leading",
            "trailing.",
            ".both,",
        ])

        song_names = self.song_scrounger.find_names(text)

        song_names_list = list(song_names)
        self.assertEqual(len(song_names_list), 3)
        self.assertEqual(set(song_names_list), set([",leading", "trailing", ".both"]))

    async def test_find_media_items__single_item_with_matching_artist__returns_that_version_only(self):
        text = "\"Sorry\" by Justin Bieber."
        self.song_scrounger._get_paragraphs = MagicMock(
            return_value=[text]
        )
        self.song_scrounger.find_names = MagicMock(
            return_value = ["Sorry"]
        )
        songs = [
            mock_track(
                name="Sorry",
                spotify_uri="spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                artists=[mock_artist("Justin Bieber")]
            ),
            mock_track(
                name="Sorry",
                spotify_uri="spotify:track:6rAXHPd18PZ6W8m9EectzH",
                artists=[mock_artist("Nothing But Thieves")]
            )
        ]
        self.mock_spotify_client.find_song = AsyncMock(
            return_value = set(songs)
        )
        self.song_scrounger.filter_if_any_artists_mentioned_greedy = MagicMock(
            return_value = set([songs[0]]))
        self.song_scrounger.reduce_by_popularity_per_artist = MagicMock(
            return_value = set([songs[0]]))

        results = await self.song_scrounger.find_media_items(text, self.mock_spotify_client.find_song)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        self.assertEqual(results["Sorry"], set([songs[0]]))

    async def test_find_media_items__same_item_mentioned_twice__returns_only_one_copy(self):
        text = "\"Sorry\" by Justin Bieber... as I said, \"Sorry\"..."
        self.song_scrounger._get_paragraphs = MagicMock(
            return_value=[text]
        )
        self.song_scrounger.find_names = MagicMock(
            return_value = ["Sorry", "Sorry"]
        )
        songs = [
            mock_track(
                name="Sorry",
                spotify_uri="spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                artists=[mock_artist("Justin Bieber")]
            )
        ]
        self.mock_spotify_client.find_song = AsyncMock(
            return_value = set(songs)
        )
        self.song_scrounger.filter_if_any_artists_mentioned_greedy = MagicMock(
            return_value = set(songs))
        self.song_scrounger.reduce_by_popularity_per_artist = MagicMock(
            return_value = set(songs))

        results = await self.song_scrounger.find_media_items(text, self.mock_spotify_client.find_song)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        self.assertEqual(results["Sorry"], set(songs))

    async def test_find_media_items__homonym_items_w_different_artists__returns_both_versions(self):
        text = "\"Sorry\" by Justin Bieber...\"Sorry\" by Nothing But Thieves"
        self.song_scrounger._get_paragraphs = MagicMock(return_value=[
            "\"Sorry\" by Justin Bieber...\"Sorry\" by Nothing But Thieves"])
        self.song_scrounger.find_names = MagicMock(
            return_value = ["Sorry"]
        )
        songs = [
            mock_track(
                name="Sorry",
                spotify_uri="spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                spotify_id="09CtPGIpYB4BrO8qb1RGsF",
                artists=[mock_artist("Justin Bieber")]
            ),
            mock_track(
                name="Sorry",
                spotify_uri="spotify:track:6rAXHPd18PZ6W8m9EectzH",
                spotify_id="6rAXHPd18PZ6W8m9EectzH",
                artists=[mock_artist("Nothing But Thieves")]
            )
        ]
        self.mock_spotify_client.find_track = AsyncMock(
            return_value = set(songs)
        )
        self.song_scrounger.filter_if_any_artists_mentioned = MagicMock(
            return_value = set(songs))
        self.song_scrounger.reduce_by_popularity_per_artist = MagicMock(
            return_value = set(songs))

        results = await self.song_scrounger.find_media_items(text, self.mock_spotify_client.find_track)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 2)
        self.assertEqual(results["Sorry"], set(songs))

    async def test_find_media_items__multiple_search_results_w_same_artist__returns_only_one(self):
        text = "\"American Pie\" by Don McLean"
        self.song_scrounger._get_paragraphs = MagicMock(return_value=[text])
        self.song_scrounger.find_names = MagicMock(
            return_value = ["American Pie"]
        )
        less_popular_version = mock_track(
            name="American Pie",
            spotify_uri="spotify:track:1fDsrQ23eTAVFElUMaf38X",
            artists=[mock_artist("Don McLean")],
            popularity=1
        )
        more_popular_version = mock_track(
            name="American Pie",
            spotify_uri="spotify:track:2ZbTw8awL7EFat9Wz1DIHN",
            artists=[mock_artist("Don McLean")],
            popularity=2
        )
        songs = [less_popular_version, more_popular_version]
        self.mock_spotify_client.find_track = AsyncMock(
            return_value = set(songs))
        self.song_scrounger.filter_if_any_artists_mentioned = MagicMock(
            return_value = set(songs))
        self.song_scrounger.reduce_by_popularity_per_artist = MagicMock(
            return_value = set([more_popular_version]))

        results = await self.song_scrounger.find_media_items(text, self.mock_spotify_client.find_track)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("American Pie" in results.keys())
        self.assertEqual(len(results["American Pie"]), 1)
        self.assertEqual(results["American Pie"], set([more_popular_version]))

    async def test_find_media_items__single_album(self):
        text = "\"Sweetener\" by Ariana Grande."
        albums = [
            mock_album(
                name="Sweetener",
                #"https://open.spotify.com/album/3tx8gQqWbGwqIGZHqDNrGe?si=FiUckKM4QIq0OlNdEQGrVw",
                spotify_uri="spotify:album:3tx8gQqWbGwqIGZHqDNrGe",
                spotify_id="3tx8gQqWbGwqIGZHqDNrGe",
                artists=[mock_artist("Ariana Grande")],
            )
        ]
        self.song_scrounger._get_paragraphs = MagicMock(
            return_value=[text]
        )
        self.song_scrounger.find_names = MagicMock(
            return_value = ["Sweetener"]
        )
        self.mock_spotify_client.find_album = AsyncMock(
            return_value = set(albums)
        )
        self.song_scrounger.filter_if_any_artists_mentioned_greedy = MagicMock(
            return_value = set([albums[0]]))
        self.song_scrounger.reduce_by_popularity_per_artist = MagicMock(
            return_value = set([albums[0]]))

        results = await self.song_scrounger.find_media_items(text, self.mock_spotify_client.find_album)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sweetener" in results.keys())
        self.assertEqual(len(results["Sweetener"]), 1)
        self.assertEqual(results["Sweetener"], set([albums[0]]))

    async def test_filter_if_any_artists_mentioned_greedy__no_matching_artist_in_cur_paragraph_and_multiple_matching_songs__finds_artist_elsewhere_in_doc(self):
        song_w_matching_artist = mock_track(
            name="American Pie",
            spotify_uri="spotify:track:1fDsrQ23eTAVFElUMaf38X",
            artists=[mock_artist("Don McLean")],
        )
        songs = set([
            song_w_matching_artist,
            mock_track(
                name="American Pie",
                spotify_uri="spotify:track:xxxxxxxxxxxxxxxxxxxxxx",
                artists=[mock_artist("Some other dude")],
            )
        ])
        self.song_scrounger.filter_if_any_artists_mentioned = MagicMock(
            side_effect = [songs, [song_w_matching_artist]])

        results = self.song_scrounger.filter_if_any_artists_mentioned_greedy(
            songs,
            "\"American Pie\" by someone...",
            "\"American Pie\" by someone...\nOh yeah, by Don McLean"
        )

        results = list(results)
        self.assertEqual(len(results), 1)
        self.assertEqual("American Pie", results[0].name)
        self.assertEqual(1, len(results[0].artists))
        self.assertEqual("Don McLean", results[0].artists[0].name)
        self.assertEqual(
            "spotify:track:1fDsrQ23eTAVFElUMaf38X",
            results[0].spotify_uri
        )

    async def test_filter_if_any_artists_mentioned_greedy__immediate_matching_artist__avoid_extra_search_call(self):
        songs = [mock_track(
            name="American Pie",
            spotify_uri="spotify:track:1fDsrQ23eTAVFElUMaf38X",
            artists=[mock_artist("Don McLean")],
        )]
        self.song_scrounger.filter_if_any_artists_mentioned = MagicMock(
            return_value = set(songs))

        results = self.song_scrounger.filter_if_any_artists_mentioned_greedy(
            songs,
            "\"American Pie\" by Don McLean",
            "\"American Pie\" by Don McLean"
        )

        results = list(results)
        self.song_scrounger.filter_if_any_artists_mentioned.assert_called_once_with(
            songs, "\"American Pie\" by Don McLean")
        self.assertEqual(len(results), 1)
        self.assertEqual("American Pie", results[0].name)
        self.assertEqual(1, len(results[0].artists))
        self.assertEqual("Don McLean", results[0].artists[0].name)
        self.assertEqual(
            "spotify:track:1fDsrQ23eTAVFElUMaf38X",
            results[0].spotify_uri
        )

    async def test_set_union__no_dups__keeps_all(self):
        song_A = mock_track("Song A", "URI A", "Artist A")
        song_B = mock_track("Song B", "URI B", "Artist B")

        set_union = self.song_scrounger.set_union(set([song_A]), set([song_B]))

        self.assertEqual(len(set_union), 2)
        self.assertTrue(song_A in set_union)
        self.assertTrue(song_B in set_union)

    async def test_set_union__all_dups__keeps_one(self):
        song_A = mock_track("Song A", "URI A", "Artist A")
        song_A_dup = mock_track("Song A", "URI A", "Artist A")

        set_union = self.song_scrounger.set_union(set([song_A]), set([song_A_dup]))

        self.assertEqual(len(set_union), 1)
        self.assertTrue(song_A in set_union or song_A_dup in set_union)

    async def test_set_union__one_dups__removes_dup_keeps_others(self):
        song_A = mock_track("Song A", "URI A", "Artist A")
        song_B = mock_track("Song B", "URI B", "Artist B")
        song_B_dup = mock_track("Song B", "URI B", "Artist B")
        song_C = mock_track("Song C", "URI C", "Artist C")

        set_union = self.song_scrounger.set_union(set([song_A, song_B]), set([song_B_dup, song_C]))

        self.assertEqual(len(set_union), 3)
        self.assertTrue(song_A in set_union)
        self.assertTrue(song_B in set_union or song_B_dup in set_union)
        self.assertTrue(song_C in set_union)

    async def test_filter_if_any_artists_mentioned__only_keeps_mentioned_artist(self):
        text = "\"Sorry\""
        songs = [
            mock_track(
                name="Sorry",
                spotify_uri="spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                artists=[mock_artist("Justin Bieber")]
            ),
            mock_track(
                name="Sorry",
                spotify_uri="spotify:track:6rAXHPd18PZ6W8m9EectzH",
                artists=[mock_artist("Nothing But Thieves")]
            )
        ]
        self.song_scrounger.filter_by_mentioned_artist = MagicMock(
            return_value = set([songs[0]])
        )

        filtered_songs = self.song_scrounger.filter_if_any_artists_mentioned(songs, text)

        self.song_scrounger.filter_by_mentioned_artist.assert_called_once_with(
            songs, text)
        self.assertEqual(filtered_songs, set([songs[0]]))

    async def test_filter_if_any_artists_mentioned__no_artist_mentioned__keeps_all_songs(self):
        text = "\"Sorry\""
        songs = [
            mock_track(
                name="Sorry",
                spotify_uri="spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                artists=[mock_artist("Justin Bieber")]
            ),
            mock_track(
                name="Sorry",
                spotify_uri="spotify:track:6rAXHPd18PZ6W8m9EectzH",
                artists=[mock_artist("Nothing But Thieves")]
            )
        ]
        self.song_scrounger.filter_by_mentioned_artist = MagicMock(
            return_value = set()
        )

        filtered_songs = self.song_scrounger.filter_if_any_artists_mentioned(songs, text)

        self.song_scrounger.filter_by_mentioned_artist.assert_called_once_with(
            songs, text
        )
        self.assertEqual(filtered_songs, set(songs))

    async def test_filter_by_mentioned_artist__only_returns_song_by_mentioned_artist(self):
        text = "\"Sorry\" by Justin Bieber"
        song_by_mentioned_artist = mock_track(
            name="Sorry",
            spotify_uri="spotify:track:09CtPGIpYB4BrO8qb1RGsF",
            artists=[mock_artist(name="Justin Bieber")]
        )
        song_by_unmentioned_artist = mock_track(
            name="Sorry",
            spotify_uri="spotify:track:6rAXHPd18PZ6W8m9EectzH",
            artists=[mock_artist(name="Nothing But Thieves")]
        )
        self.song_scrounger.is_mentioned = MagicMock(side_effect=[True, False, False, False])

        filtered_songs = self.song_scrounger.filter_by_mentioned_artist(
            [song_by_mentioned_artist, song_by_unmentioned_artist], text)

        self.song_scrounger.is_mentioned.assert_any_call("Justin Bieber", text)
        self.song_scrounger.is_mentioned.assert_any_call("Nothing But Thieves", text)
        self.assertEqual(len(filtered_songs), 1)
        self.assertEqual(list(filtered_songs)[0], song_by_mentioned_artist)

    async def test_filter_by_mentioned_artist__no_artists_mentioned__returns_empty_set(self):
        text = "\"Sorry\" by ... someone"
        songs = [mock_track(
            name="Sorry",
            spotify_uri="spotify:track:09CtPGIpYB4BrO8qb1RGsF",
            artists=[mock_artist(name="Justin Bieber")]
        )]
        self.song_scrounger.is_mentioned_verbatim = MagicMock(return_value=False)

        filtered_songs = self.song_scrounger.filter_by_mentioned_artist(songs, text)

        self.song_scrounger.is_mentioned_verbatim.assert_any_call("Justin Bieber", text)
        self.assertEqual(len(filtered_songs), 0)

    async def test_filter_by_mentioned_artist__multiple_artist_per_song__skips_duplicates(self):
        text = "\"Sorry\" by Billie Eilish and brother Finneas O'Connell"
        songs = [mock_track(
            name="bad guy",
            spotify_uri="spotify:track:2Fxmhks0bxGSBdJ92vM42m",
            artists=[mock_artist("Billie Eilish"), mock_artist("Finneas O'Connell")]
        )]
        self.song_scrounger.is_mentioned_verbatim = MagicMock(return_value=True)

        filtered_songs = self.song_scrounger.filter_by_mentioned_artist(songs, text)

        self.assertTrue(
            get_num_times_called(self.song_scrounger.is_mentioned_verbatim) >= 1)
        self.assertEqual(len(filtered_songs), 1)
        filtered_songs_list = list(filtered_songs)
        self.assertEqual(filtered_songs_list[0].name, "bad guy")
        self.assertEqual(filtered_songs_list[0].spotify_uri, "spotify:track:2Fxmhks0bxGSBdJ92vM42m")
        self.assertEqual(2, len(filtered_songs_list[0].artists))
        self.assertEqual("Billie Eilish", filtered_songs_list[0].artists[0].name)
        self.assertEqual("Finneas O'Connell", filtered_songs_list[0].artists[1].name)

    @unittest.skip("Enable when implemented")
    async def test_filter_by_mentioned_artist__song_name_artist_name_clash(self):
        # TODO: what if a song name is found as an artist name?
        pass

    async def test_reduce_by_popularity_per_artist__by_same_artist__reduces_to_one(self):
        songs = [
            mock_track(
                name="American Pie",
                spotify_uri="spotify:track:1fDsrQ23eTAVFElUMaf38X",
                artists=[mock_artist("Don McLean")]
            ),
            mock_track(
                name="American Pie",
                spotify_uri="spotify:track:4wpuHehFEEpWAlkw3vjH0s",
                artists=[mock_artist("Don McLean")]
            )
        ]
        self.song_scrounger.pick_most_popular = MagicMock(
            return_value = songs[0])

        results = self.song_scrounger.reduce_by_popularity_per_artist(songs)

        self.song_scrounger.pick_most_popular.assert_called_once_with(set(songs))
        self.assertEqual(len(results), 1)
        self.assertEqual(list(results)[0], songs[0])

    async def test_reduce_by_popularity_per_artist__by_diff_artists__does_not_reduce(self):
        song_by_artist1 = mock_track(
            name="American Pie",
            spotify_uri="spotify:track:1fDsrQ23eTAVFElUMaf38X",
            spotify_id="1fDsrQ23eTAVFElUMaf38X",
            artists=[mock_artist("Don McLean")]
        )
        song_by_artist2 = mock_track(
            name="American Pie",
            spotify_uri="spotify:track:1vo6TY0FyLRBTXohxvflhJ",
            spotify_id="1vo6TY0FyLRBTXohxvflhJ",
            artists=[mock_artist("Madonna")]
        )
        songs = [song_by_artist1, song_by_artist2]
        def pick_most_popular__ret_vals(songs):
            songs = list(songs)
            if len(songs) != 1:
                raise ValueError(f"Mock did expected list of len==1: {songs}")
            elif "Don McLean" in songs[0].artists[0].name:
                return song_by_artist1
            elif "Madonna" in songs[0].artists[0].name:
                return song_by_artist2
            else:
                raise ValueError(f"Mock did not expect arg: {songs}")
        self.song_scrounger.pick_most_popular = MagicMock(
            side_effect = pick_most_popular__ret_vals)

        results = self.song_scrounger.reduce_by_popularity_per_artist(songs)

        self.assertEqual(len(results), 2)
        self.assertTrue(song_by_artist1 in results)
        self.assertTrue(song_by_artist2 in results)

    async def test_pick_most_popular__two_songs_w_diff_popularity__picks_most_popular(self):
        less_popular_song = mock_track(
            "some song",
            "some spotify uri",
            artists=[mock_artist("some artist")],
            popularity=1
        )
        more_popular_song = mock_track(
            "mock name of more popular version",
            "mock spotify uri of more popular version",
            artists=[mock_artist("mock artist of more popular version")],
            popularity=2
        )
        mock_songs = [less_popular_song, more_popular_song]

        result = self.song_scrounger.pick_most_popular(mock_songs)

        self.assertEqual(result, more_popular_song)

    async def test_pick_most_popular__multiple_songs_w_diff_popularity__picks_most_popular(self):
        less_popular_song = mock_track(
            name="some song",
            spotify_uri="some spotify uri",
            artists=[mock_artist("some artist")],
            popularity=1
        )
        another_less_popular_song = mock_track(
            name="some song",
            spotify_uri="some spotify uri",
            artists=[mock_artist("some artist")],
            popularity=25
        )
        yet_another_less_popular_song = mock_track(
            name="some song",
            spotify_uri="some spotify uri",
            artists=[mock_artist("some artist")],
            popularity=50
        )
        more_popular_song = mock_track(
            name="mock name of more popular version",
            spotify_uri="mock spotify uri of more popular version",
            artists=[mock_artist("mock artist of more popular version")],
            popularity=100
        )
        mock_songs = [
            less_popular_song,
            another_less_popular_song,
            yet_another_less_popular_song,
            more_popular_song
        ]

        result = self.song_scrounger.pick_most_popular(mock_songs)

        self.assertEqual(result, more_popular_song)

    async def test_pick_most_popular__only_one_song__defaults_to_that_song(self):
        some_song = mock_track(
            "mock song", "mock spotify uri", ["mock artist"], popularity=1)

        result = self.song_scrounger.pick_most_popular([some_song])

        self.assertEqual(result, some_song)

    async def test_pick_most_popular__compares_undefined_popularity__raises(self):
        song_w_undefined_popularity = mock_track(
            "mock song", "mock spotify uri", ["mock artist"], popularity=None)

        with self.assertRaises(ValueError):
            result = self.song_scrounger.pick_most_popular([
                song_w_undefined_popularity, song_w_undefined_popularity])

    async def test_get_paragraphs__no_newlines(self):
        text = "Only paragraph"

        paragraphs = self.song_scrounger._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 1)
        self.assertEqual(paragraphs[0], "Only paragraph")

    async def test_get_paragraphs__splits_by_newline(self):
        text = "Paragraph one\nParagraph two"

        paragraphs = self.song_scrounger._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0], "Paragraph one")
        self.assertEqual(paragraphs[1], "Paragraph two")

    async def test_get_paragraphs__omits_empty_paragraph(self):
        text = "Paragraph one\n\nParagraph two"

        paragraphs = self.song_scrounger._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0], "Paragraph one")
        self.assertEqual(paragraphs[1], "Paragraph two")

    async def test_get_paragraphs__omits_whitespace_paragraph(self):
        text = "Paragraph one\n   \nParagraph two"

        paragraphs = self.song_scrounger._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0], "Paragraph one")
        self.assertEqual(paragraphs[1], "Paragraph two")

    async def test_is_partially_mentioned__true(self):
        word, text = "Lonnie Donnegan & His Skiffle Group", "Lonnie Donnegan was a solo artist"

        is_mentioned = self.song_scrounger.is_partially_mentioned(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_partially_mentioned__true2(self):
        word, text = "Lonnie Donnegan and His Skiffle Group", "Lonnie Donnegan was a solo artist"

        is_mentioned = self.song_scrounger.is_partially_mentioned(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_partially_mentioned__true3(self):
        word, text = "Lonnie Donnegan Band", "Lonnie Donnegan was a solo artist"

        is_mentioned = self.song_scrounger.is_partially_mentioned(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_partially_mentioned__single_word__splits_safely(self):
        word, text = "Cher", "Doesn't matter"

        # Assert does not cause exception
        is_mentioned = self.song_scrounger.is_partially_mentioned(word, text)

    async def test_is_mentioned_verbatim__true(self):
        word, text = "Justin Bieber", "Hey, it's Justin Bieber"

        is_mentioned = self.song_scrounger.is_mentioned_verbatim(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned_verbatim__ignores_case(self):
        word, text = "JUSTIN bieber", "Hey, it's Justin Bieber"

        is_mentioned = self.song_scrounger.is_mentioned_verbatim(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned_verbatim__false(self):
        word, text = "Justin Bieber", "Oh no, it's Justin Timberlake"

        is_mentioned = self.song_scrounger.is_mentioned_verbatim(word, text)

        self.assertFalse(is_mentioned)

    async def test_is_partially_mentioned__tokens_match_separately__counted_as_mention(self):
        # actual example: http://www.dntownsend.com/Site/Rock/3change.htm
        word, text = "Paul Anka", "Paul (\"Put Your Head on My Shoulder\") Anka"

        is_mentioned_in_parts = self.song_scrounger.is_mentioned_in_parts(word, text)

        self.assertTrue(is_mentioned_in_parts)

    # NOTE: Regression Test
    async def test_is_mentioned_in_parts__token_found_as_substr__not_counted_as_mention(self):
        # Bug: 'Stones' matched with 'Stone' and 'allen' with 'challenged'
        word, text = "Allen Stone", "The Rolling Stones challenged the Beatles to a game of foosball"

        is_mentioned_in_parts = self.song_scrounger.is_mentioned_in_parts(word, text)

        self.assertFalse(is_mentioned_in_parts)

    async def test_is_mentioned_as_full_str__mentioned_in_diff_casing__ignores_occurrence(self):
        word, text = "HELLO", "Hello"

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertFalse(is_mentioned)

    async def test_is_mentioned_as_full_str__mentioned_between_spaces__finds_occurrence(self):
        word, text = "The Rolling Stones", "... The Rolling Stones ..."

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned_as_full_str__mentioned_at_end__finds_occurrence(self):
        word, text = "The Rolling Stones", "..by The Rolling Stones"

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned_as_full_str__mentioned_at_beginning__finds_occurrence(self):
        word, text = "The Rolling Stones", "The Rolling Stones played.."

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned_as_full_str__mentioned_between_punctuation__finds_occurrence(self):
        word = "The Rolling Stones"
        text_period_comma = ".The Rolling Stones,"
        text_quote_apostrophe = "\"The Rolling Stones's"

        is_mentioned_period_comma = self.song_scrounger.is_mentioned_as_full_str(
            word, text_period_comma)
        is_mentioned_quote_apostrophe = self.song_scrounger.is_mentioned_as_full_str(
            word, text_quote_apostrophe)

        self.assertTrue(is_mentioned_period_comma)
        self.assertTrue(is_mentioned_quote_apostrophe)

    async def test_is_mentioned_as_full_str__mentioned_as_substr__ignores_occurrence(self):
        word, text = "allen", "Challenged"

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertFalse(is_mentioned)

    async def test_is_mentioned_as_full_str__matches_synonym__symbol_to_word(self):
        word, text = "&", "This and that"

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned_as_full_str__matches_synonym__word_to_symbol(self):
        word, text = "and", "This & that"

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertTrue(is_mentioned)

    @patch("packages.song_scrounger.song_scrounger.read_file_contents", return_value="When Don McLean recorded \"American Pie\"")
    async def test_find_songs__mocked_spotify_client__song_w_single_artist(self, mock_read_file_contents):
        self.mock_spotify_client.find_song.return_value = [
            mock_track(
                name="American Pie",
                spotify_uri="spotify:track:1fDsrQ23eTAVFElUMaf38X",
                artists=[mock_artist("Don McLean")],
                popularity=None
            ),
        ]

        results = await self.song_scrounger.find_songs("mock file path")

        mock_read_file_contents.assert_called_once_with("mock file path")
        self.mock_spotify_client.find_song.assert_any_call("American Pie")
        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        self.assertEqual(len(results["American Pie"]), 1)
        self.assertEqual(
            set([song.spotify_uri for song in results["American Pie"]]),
            set(["spotify:track:1fDsrQ23eTAVFElUMaf38X"]))

    @patch("packages.song_scrounger.song_scrounger.read_file_contents", return_value="The song \"Time Is On My Side\" by the Rolling Stones cannot be found verbatim on Spotify")
    async def test_find_songs__spotify_song_title_contains_metadata__song_is_matched_regardless(
        self, mock_read_file_contents):
        self.mock_spotify_client.find_song.return_value = [
            mock_track(
                "Time Is On My Side - Mono Version",
                spotify_uri="spotify:track:2jaN6NgXflZTj2z9CWcqaP",
                artists=[mock_artist("The Rolling Stones")],
                popularity=None
            ),
            mock_track(
                "Time Is On My Side",
                spotify_uri="spotify:track:6IpxLzChgCbFSJwso2Q84D",
                artists=[mock_artist("Irma Thomas")],
                popularity=None
            ),
        ]

        results = await self.song_scrounger.find_songs("mock file path")

        mock_read_file_contents.assert_called_once_with("mock file path")
        self.mock_spotify_client.find_song.assert_any_call("Time Is On My Side")
        self.assertEqual(1, len(results.keys()))
        self.assertIn("Time Is On My Side", results.keys())
        self.assertEqual(len(results["Time Is On My Side"]), 1)
        self.assertEqual(
            set([song.spotify_uri for song in results["Time Is On My Side"]]),
            set(["spotify:track:2jaN6NgXflZTj2z9CWcqaP"]))
        self.assertEqual(1, len(list(results["Time Is On My Side"])[0].artists))
        self.assertIn("The Rolling Stones", list(results["Time Is On My Side"])[0].artists[0].name)

    # NOTE: 'Allen' is a substr of 'challenges', and 'Stone' of 'stoned'
    @patch("packages.song_scrounger.song_scrounger.read_file_contents", return_value="The song \"Satisfaction\" challenges stoned hippies")
    async def test_find_songs__artist_name_appears_as_substr_only__artist_not_matched(
        self, mock_read_file_contents):
        # NOTE: its important that the spotify URIs don't match
        self.mock_spotify_client.find_song.return_value = [
            mock_track(
                "Satisfaction",
                spotify_uri="spotify:track:mock1",
                spotify_id="mock1",
                artists=[mock_artist("MOCKARTIST")],
            ),
            mock_track(
                "Satisfaction",
                spotify_uri="spotify:track:mock2",
                spotify_id="mock2",
                artists=[mock_artist("Allen Stone")],
            ),
        ]

        results = await self.song_scrounger.find_songs("mock file path")

        mock_read_file_contents.assert_called_once_with("mock file path")
        self.mock_spotify_client.find_song.assert_any_call("Satisfaction")
        self.assertEqual(len(results.keys()), 1)
        self.assertEqual(len(results["Satisfaction"]), 2)
        artists = [artist.name for artist in list(results["Satisfaction"])[0].artists] + [artist.name for artist in list(results["Satisfaction"])[1].artists]
        self.assertIn("MOCKARTIST", artists)
        self.assertIn("Allen Stone", artists)

    @patch("packages.song_scrounger.song_scrounger.read_file_contents", return_value="\"Mock Song Name\"")
    async def test_find_songs__song_dups_same_artist__returns_most_popular_version_only(
        self, mock_read_file_contents):
        self.mock_spotify_client.find_song.return_value = [
            mock_track(
                name="Mock Song Name",
                spotify_uri="spotify:track:mock1",
                artists=[mock_artist("MOCKARTIST")],
                popularity=1
            ),
            mock_track(
                name="Mock Song Name",
                spotify_uri="spotify:track:mock2",
                artists=[mock_artist("MOCKARTIST")],
                popularity=50
            ),
            mock_track(
                name="Mock Song Name",
                spotify_uri="spotify:track:mock3",
                artists=[mock_artist("MOCKARTIST")],
                popularity=100
            )
        ]

        results = await self.song_scrounger.find_songs("mock file path")

        mock_read_file_contents.assert_called_once_with("mock file path")
        self.mock_spotify_client.find_song.assert_called_once_with("Mock Song Name")
        self.assertEqual(len(results.keys()), 1)
        self.assertEqual(len(results["Mock Song Name"]), 1)

    @patch(
        "packages.song_scrounger.song_scrounger.read_file_contents",
        return_value="\"Mock Song Name\" by Mock Artist\nOther Mock Artist"
    )
    async def test_find_songs__multiple_artists_match__prefers_artist_in_same_paragraph(self, mock_read_file_contents):
        self.mock_spotify_client.find_song.return_value = [
            mock_track(
                name="Mock Song Name",
                spotify_uri="spotify:track:mock1",
                artists=[mock_artist("Mock Artist")],
                popularity=1
            ),
            mock_track(
                name="Mock Song Name",
                spotify_uri="spotify:track:mock2",
                artists=[mock_artist("Other Mock Artist")],
                popularity=1
            )
        ]

        results = await self.song_scrounger.find_songs("mock file path")

        mock_read_file_contents.assert_called_once_with("mock file path")
        self.mock_spotify_client.find_song.assert_called_once_with("Mock Song Name")
        self.assertEqual(len(results.keys()), 1)
        self.assertEqual(len(results["Mock Song Name"]), 1)
        self.assertEqual(list(results["Mock Song Name"])[0].name, "Mock Song Name")
        self.assertEqual(list(results["Mock Song Name"])[0].spotify_uri, "spotify:track:mock1")
        self.assertEqual(len(list((results["Mock Song Name"]))[0].artists), 1)
        self.assertEqual(len(list(results["Mock Song Name"])[0].artists), 1)
        self.assertEqual(list(results["Mock Song Name"])[0].artists[0].name, "Mock Artist")

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__song_w_single_artist(self):
        input_file_name = "single_artist_mentioned.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        self.assertEqual(len(results["American Pie"]), 1)
        self.assertEqual(
            set([song.spotify_uri for song in results["American Pie"]]),
            set(["spotify:track:1fDsrQ23eTAVFElUMaf38X"])
        )

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__two_artists_one_song(self):
        input_file_name = "two_artists_mentioned.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        self.assertEqual(len(results["American Pie"]), 2)
        self.assertEqual(
            set([song.spotify_uri for song in results["American Pie"]]),
            set(["spotify:track:1fDsrQ23eTAVFElUMaf38X", "spotify:track:4wpuHehFEEpWAlkw3vjH0s"])
        )

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__no_artists_filtered__multiple_results_without_duplicate_artists(self):
        input_file_name = "no_artists_mentioned.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        artist_count = defaultdict(int)
        for song in results["American Pie"]:
            artist_count["-".join(song.artists)] += 1
        for artist_count, count in artist_count.items():
            self.assertEqual(count, 1, f"{artist_count} has {count}")
        self.assertGreater(len(results["American Pie"]), 10)

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__for_duplicate_song_names(self):
        input_file_name = "test_duplicate_songs.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        self.assertIsNotNone(list(results["Sorry"])[0])
        self.assertEqual(list(results["Sorry"])[0].name, "Sorry")
        self.assertIn("spotify:track:09CtPGIpYB4BrO8qb1RGsF", list(results["Sorry"])[0].spotify_uri)
        self.assertEqual(len(list(results["Sorry"])[0].artists), 1)

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__simple_artist_detection(self):
        input_file_name = "test_simple_artist_detection.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        song = list(results["Sorry"])[0]
        self.assertIsNotNone(song)
        self.assertEqual(song.name, "Sorry")
        self.assertEqual(song.spotify_uri, "spotify:track:6rAXHPd18PZ6W8m9EectzH")
        self.assertEqual(len(song.artists), 1)
        self.assertEqual(song.artists, ["Nothing But Thieves"])

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__multi_paragraph_artist_detection(self):
        input_file_name = "test_multiparagraph_artist_detection.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 2)
        song_list = list(results["Sorry"])
        self.assertIsNotNone(song_list[0])
        self.assertIsNotNone(song_list[1])
        self.assertEqual(song_list[0].name, "Sorry")
        self.assertEqual(song_list[1].name, "Sorry")
        self.assertIn(
            "spotify:track:6rAXHPd18PZ6W8m9EectzH",
            [song_list[0].spotify_uri, song_list[1].spotify_uri]
        )
        self.assertIn(
            "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
            [song_list[0].spotify_uri, song_list[1].spotify_uri]
        )
        self.assertEqual(len(song_list[0].artists), 1)
        self.assertEqual(len(song_list[1].artists), 1)
        self.assertIn(
            "Nothing But Thieves",
            [song_list[0].artists[0], song_list[1].artists[0]]
        )
        self.assertIn(
            "Justin Bieber",
            [song_list[0].artists[0], song_list[1].artists[0]]
        )

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__cross_paragraph_artist_detection(self):
        input_file_name = "test_cross_paragraph_artist_detection.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Socially Awkward" in results.keys())
        self.assertEqual(len(results["Socially Awkward"]), 1)
        song = list(results["Socially Awkward"])[0]
        self.assertIsNotNone(song)
        self.assertEqual(song.name, "Socially Awkward")
        self.assertEqual(song.spotify_uri, "spotify:track:2yE3omg2KMRfFw4ukBlDIJ")
        self.assertEqual(len(song.artists), 1)
        self.assertEqual(song.artists, ["Kiefer"])

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__real_world_input_example(self):
        input_file_name = "history_rock_n_roll_ch4_snippet.txt"
        expected_songs = [
            "Heartbreaker", "Satisfaction", "(I Can't Get No) Satisfaction",
            "Doo Doo Doo Doo Doo (Heartbreaker)", "Time is On My Side",
            "Livin' Doll", "Halfway to Paradise", "Rock with the Caveman",
            "Rock Island Line", "Doo Doo Doo Doo Doo",
            """Why don't we put that doo-doo stuff in the title
            so the kids will know which one they're buying?"""
        ].sort()


        results = await self._run_find_songs_test(input_file_name)


        self.assertEqual(len(results.keys()), 11)
        self.assertEqual(list(results.keys()).sort(), expected_songs)

        # PROB: Grand Funk Railroad not detected bc it is mentioned as 'Grank Funk'
        self.assertEqual(len(results["Heartbreaker"]), 1)
        self.assertIn("Led Zeppelin", list(results["Heartbreaker"])[0].artists)

        # (It's ok that it's not detected as a Rolling Stones song bc they name it something else)
        self.assertEqual(len(results["Satisfaction"]), 15)

        self.assertEqual(len(results["(I Can't Get No) Satisfaction"]), 1)
        self.assertIn(
            "The Rolling Stones",
            list(results["(I Can't Get No) Satisfaction"])[0].artists
        )

        self.assertEqual(len(results["Time is On My Side"]), 1)
        self.assertIn(
            "The Rolling Stones",
            list(results["Time is On My Side"])[0].artists
        )

        # might match both 'Billy Fury' and 'Billy Fury and The Tornados'
        self.assertLessEqual(len(results["Halfway to Paradise"]), 2)
        for song in results["Halfway to Paradise"]:
            self.assertIn(
                "Billy Fury",
                song.artists[0]
            )

        self.assertEqual(len(results["Rock with the Caveman"]), 2)
        rock_w_caveman_results = list(results["Rock with the Caveman"])
        self.assertTrue(
            "Tommy Steele" in rock_w_caveman_results[0].artists or
            "Tommy Steele" in rock_w_caveman_results[1].artists
        )
        self.assertTrue(
            "Tommy Steele & The Steelmen" in rock_w_caveman_results[0].artists or
            "Tommy Steele & The Steelmen" in rock_w_caveman_results[1].artists
        )

        # matches both 'Lonnie Donnegan' and 'Lonnie Donnegan & His Skiffle Group'
        self.assertEqual(len(results["Rock Island Line"]), 2)

        # PROB: Spotify has the song as "Living Doll"
        self.assertEqual(len(results["Livin' Doll"]), 0)

        self.assertEqual(len(results["Doo Doo Doo Doo Doo"]), 0)
        self.assertEqual(
            len(results["""Why don't we put that doo-doo stuff in the title
                so the kids will know which one they're buying?"""]),
            0
        )

    async def _run_find_songs_test(self, input_file_name):
        from packages.song_scrounger.spotify_client import SpotifyClient
        from packages.song_scrounger.util import get_spotify_creds
        from tests import helper

        spotify_client_id, spotify_secret_key = get_spotify_creds()
        spotify_client = SpotifyClient(spotify_client_id, spotify_secret_key)

        song_scrounger = SongScrounger(spotify_client)
        input_file_path = helper.get_path_to_test_input_file(input_file_name)
        return await song_scrounger.find_songs(input_file_path)

    @unittest.skip("Integration tests disabled by default")
    @patch("packages.song_scrounger.song_scrounger.read_file_contents", return_value="\"Revolver\" by The Beatles")
    async def test_find_albums__artists_mentioned__gets_all_songs(self, _):
        results = await self._run_find_albums_test("mock file path")

        self.assertEqual(len(results.keys()), 1)
        self.assertIn("Revolver", results)
        self.assertEqual(len(results["Revolver"]), 1)
        self.assertEqual(len(list(results["Revolver"])[0].artists), 1)
        self.assertEqual(list(results["Revolver"])[0].artists[0].name, "The Beatles")
        self.assertEqual(len(list(results["Revolver"])[0].tracks), 14)
        self.assertEqual(list(results["Revolver"])[0].tracks[0].name, "Taxman - Remastered 2009")
        self.assertEqual(list(results["Revolver"])[0].tracks[-1].name, "Tomorrow Never Knows - Remastered 2009")

    @unittest.skip("Integration tests disabled by default")
    @patch("packages.song_scrounger.song_scrounger.read_file_contents", return_value="\"Revolver\" by Slaine")
    async def test_find_albums__artists_mentioned__picks_version_by_artist(self, _):
        results = await self._run_find_albums_test("mock file path")

        self.assertEqual(len(results.keys()), 1)
        self.assertIn("Revolver", results)
        self.assertEqual(len(results["Revolver"]), 1)
        self.assertEqual(list(results["Revolver"])[0].artists, ["Slaine"])

    @unittest.skip("Integration tests disabled by default")
    @patch("packages.song_scrounger.song_scrounger.read_file_contents", return_value="\"Revolver\"")
    async def test_find_albums__no_artist__returns_multiple_results(self, _):
        results = await self._run_find_albums_test("mock file path")

        self.assertEqual(len(results.keys()), 1)
        self.assertIn("Revolver", results)
        self.assertLess(1, len(results["Revolver"]))
        found_beatles_album = TestSongScroungerHelper.is_one_of_the_artists(results["Revolver"], "The Beatles")
        self.assertTrue(found_beatles_album, "Expected to find album by The Beatles")

    @unittest.skip("Integration tests disabled by default")
    @patch("packages.song_scrounger.song_scrounger.read_file_contents", return_value="\"Revolver\", \"Highway 61 Revisited\", \"Pet Sounds\"")
    async def test_find_albums__multiple_albums__finds_all(self, _):
        results = await self._run_find_albums_test("mock file path")


        self.assertEqual(len(results.keys()), 3)

        self.assertIn("Revolver", results)
        self.assertLess(1, len(results["Revolver"]))
        found_beatles_album = TestSongScroungerHelper.is_one_of_the_artists(results["Revolver"], "The Beatles")
        self.assertTrue(found_beatles_album, "Expected to find album by The Beatles")

        self.assertIn("Highway 61 Revisited", results)
        self.assertLess(1, len(results["Highway 61 Revisited"]))
        found_bob_dylan_album = TestSongScroungerHelper.is_one_of_the_artists(results["Highway 61 Revisited"], "Bob Dylan")
        self.assertTrue(found_bob_dylan_album, "Expected to find album by Bob Dylan")

        self.assertIn("Pet Sounds", results)
        self.assertEqual(1, len(results["Pet Sounds"]))
        found_bob_dylan_album = TestSongScroungerHelper.is_one_of_the_artists(results["Pet Sounds"], "The Beach Boys")
        self.assertTrue(found_bob_dylan_album, "Expected to find album by The Beach Boys")

    async def _run_find_albums_test(self, input_file_name):
        from packages.music_api_clients.spotify import Spotify
        from packages.song_scrounger.util import get_spotify_creds
        from tests import helper

        song_scrounger = SongScrounger(Spotify())
        input_file_path = helper.get_path_to_test_input_file(input_file_name)
        return await song_scrounger.find_albums(input_file_path)

class TestSongScroungerHelper():
    @classmethod
    def is_one_of_the_artists(cls, songs_or_albums, artist_name):
        for album in songs_or_albums:
            if artist_name in [artist for artist in album.artists]:
                return True
        return False