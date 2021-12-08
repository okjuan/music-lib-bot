import unittest
from unittest.mock import MagicMock
from app.lib.music_util import MusicUtil
from app.lib.my_music_lib import MyMusicLib
from app.lib.playlist_stats import PlaylistStats
from tests.fixtures import mock_audio_features, mock_playlist, mock_track


class TestPlaylistStats(unittest.TestCase):
    def setUp(self):
        self.mock_spotify_client = MagicMock()
        self.music_util = MusicUtil(self.mock_spotify_client, MagicMock())
        self.my_music_lib = MyMusicLib(MagicMock(), MagicMock(), MagicMock())
        self.playlist_stats = PlaylistStats(self.my_music_lib, self.music_util, MagicMock())

    def test_get_audio_feature_representative_range__single_track__allows_full_range(self):
        audio_features = mock_audio_features(danceability=0.75)
        playlist = mock_playlist(
            tracks=[mock_track(audio_features=audio_features)])

        audio_feature_range = self.playlist_stats.get_audio_feature_representative_range(playlist)

        self.assertEqual(0, audio_feature_range[0].danceability)
        self.assertEqual(1, audio_feature_range[1].danceability)

    def test_get_audio_feature_representative_range__multiple_tracks__matches_range(self):
        audio_features_1 = mock_audio_features(danceability=0.95)
        audio_features_2 = mock_audio_features(danceability=0.05)
        playlist = mock_playlist(
            tracks=[
                mock_track(audio_features=audio_features_1),
                mock_track(audio_features=audio_features_2),
            ]
        )

        audio_feature_range = self.playlist_stats.get_audio_feature_representative_range(playlist)

        self.assertLessEqual(0, audio_feature_range[0].danceability)
        self.assertGreaterEqual(1, audio_feature_range[1].danceability)

    def test_get_audio_feature_representative_range__tracks_with_same_value(self):
        audio_features_1 = mock_audio_features(danceability=0.75)
        audio_features_2 = mock_audio_features(danceability=0.75)
        playlist = mock_playlist(
            tracks=[
                mock_track(audio_features=audio_features_1),
                mock_track(audio_features=audio_features_2),
            ]
        )

        audio_feature_range = self.playlist_stats.get_audio_feature_representative_range(playlist)

        self.assertEqual(0.75, audio_feature_range[0].danceability)
        self.assertEqual(0.75, audio_feature_range[1].danceability)