from app.models.audio_features import AudioFeatures
from statistics import quantiles


MIN_KEY_VALUE = 0
MAX_KEY_VALUE = 11
MIN_MODE_VALUE = 0
MAX_MODE_VALUE = 1
MIN_TIME_SIGNATURE = 1
MAX_TIME_SIGNATURE = 12

class PlaylistStats:
    def __init__(self, my_music_lib, music_util, info_logger):
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.info_logger = info_logger

    def get_playlist_with_track_audio_features(self, playlist_name):
        """
        Params:
            playlist_name (str).

        Returns:
            playlist (Playlist): with tracks that have audio_features populated.
        """
        playlist = self.my_music_lib.get_playlist_by_name(playlist_name)
        self.music_util.populate_track_audio_features(playlist)
        return playlist

    def get_popularity_representative_range(self, playlist):
        self.music_util.populate_popularity_if_absent(playlist.tracks)
        popularities = [
            track.popularity
            for track in playlist.tracks
        ]
        return min(popularities), max(popularities)

    def get_audio_feature_representative_range(self, playlist):
        """
        Params:
            playlist (Playlist): with track.audio_features populated for each track.
                Tip: use self.get_playlist_with_track_audio_features first.
        """
        danceability_min, danceability_max = self._get_audio_feature_min_and_max(
            playlist.tracks, lambda track: track.audio_features.danceability)
        energy_min, energy_max = self._get_audio_feature_min_and_max(
            playlist.tracks, lambda track: track.audio_features.energy)
        loudness_min, loudness_max = self._get_audio_feature_min_and_max(
            playlist.tracks, lambda track: track.audio_features.loudness)
        speechiness_min, speechiness_max = self._get_audio_feature_min_and_max(
            playlist.tracks, lambda track: track.audio_features.speechiness)
        acousticness_min, acousticness_max = self._get_audio_feature_min_and_max(
            playlist.tracks, lambda track: track.audio_features.acousticness)
        instrumentalness_min, instrumentalness_max = self._get_audio_feature_min_and_max(
            playlist.tracks, lambda track: track.audio_features.instrumentalness)
        liveness_min, liveness_max = self._get_audio_feature_min_and_max(
            playlist.tracks, lambda track: track.audio_features.liveness)
        valence_min, valence_max = self._get_audio_feature_min_and_max(
            playlist.tracks, lambda track: track.audio_features.valence)
        tempo_min, tempo_max = self._get_audio_feature_min_and_max(
            playlist.tracks, lambda track: track.audio_features.tempo)
        duration_ms_min, duration_ms_max = self._get_audio_feature_min_and_max(
            playlist.tracks, lambda track: track.audio_features.duration_ms)
        return (
            AudioFeatures(
                danceability_min,
                energy_min,
                MIN_KEY_VALUE,
                loudness_min,
                MIN_MODE_VALUE,
                speechiness_min,
                acousticness_min,
                instrumentalness_min,
                liveness_min,
                valence_min,
                tempo_min,
                duration_ms_min,
                MIN_TIME_SIGNATURE,
            ),
            AudioFeatures(
                danceability_max,
                energy_max,
                MAX_KEY_VALUE,
                loudness_max,
                MAX_MODE_VALUE,
                speechiness_max,
                acousticness_max,
                instrumentalness_max,
                liveness_max,
                valence_max,
                tempo_max,
                duration_ms_max,
                MAX_TIME_SIGNATURE,
            ),
        )

    def _get_audio_feature_min_and_max(self, tracks, get_audio_feature):
        return self._get_middle_quantile_min_and_max(
            [get_audio_feature(track) for track in tracks])

    def _get_middle_quantile_min_and_max(self, values):
        value_quantiles = quantiles(values)
        return value_quantiles[0], value_quantiles[-1]