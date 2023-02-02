from packages.music_api_clients.models.audio_features import AudioFeatures
from statistics import quantiles


class PlaylistAnalyzer:
    def __init__(self, my_music_lib, music_util, info_logger):
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.info_logger = info_logger

    def get_popularity_representative_range(self, playlist):
        self.music_util.populate_popularity_if_absent(playlist.get_tracks())
        popularities = [
            track.popularity
            for track in playlist.get_tracks()
        ]
        min, max = self._get_middle_quantile_min_and_max(popularities)
        return int(min), int(max)

    def get_audio_feature_representative_range(self, playlist):
        """Skips tracks that don't have audio_features set. Should call
        MusicUtil.populate_track_audio_features first.

        Params:
            playlist (Playlist): with track.audio_features populated for each track.
                Tip: use music_util.populate_track_audio_features first.

        Returns:
            (2-tuple): (AudioFeatures, AudioFeatures) min, max.
        """
        tracks = [
            track
            for track in playlist.get_tracks()
            if track.audio_features is not None
        ]
        if len(tracks) == 1:
            return (self._get_min_audio_features(), self._get_max_audio_features())

        danceability_min, danceability_max = self._get_audio_feature_min_and_max(
            [track.audio_features.danceability for track in tracks],
            AudioFeatures.MIN_PERCENTAGE,
            AudioFeatures.MAX_PERCENTAGE,
        )
        energy_min, energy_max = self._get_audio_feature_min_and_max(
            [track.audio_features.energy for track in tracks],
            AudioFeatures.MIN_PERCENTAGE,
            AudioFeatures.MAX_PERCENTAGE,
        )
        loudness_min, loudness_max = self._get_audio_feature_min_and_max(
            [track.audio_features.loudness for track in tracks],
            AudioFeatures.MIN_LOUDNESS,
            AudioFeatures.MAX_LOUDNESS,
        )
        speechiness_min, speechiness_max = self._get_audio_feature_min_and_max(
            [track.audio_features.speechiness for track in tracks],
            AudioFeatures.MIN_PERCENTAGE,
            AudioFeatures.MAX_PERCENTAGE,
        )
        acousticness_min, acousticness_max = self._get_audio_feature_min_and_max(
            [track.audio_features.acousticness for track in tracks],
            AudioFeatures.MIN_PERCENTAGE,
            AudioFeatures.MAX_PERCENTAGE,
        )
        instrumentalness_min, instrumentalness_max = self._get_audio_feature_min_and_max(
            [track.audio_features.instrumentalness for track in tracks],
            AudioFeatures.MIN_PERCENTAGE,
            AudioFeatures.MAX_PERCENTAGE,
        )
        liveness_min, liveness_max = self._get_audio_feature_min_and_max(
            [track.audio_features.valence for track in tracks],
            AudioFeatures.MIN_PERCENTAGE,
            AudioFeatures.MAX_PERCENTAGE,
        )
        valence_min, valence_max = self._get_audio_feature_min_and_max(
            [track.audio_features.valence for track in tracks],
            AudioFeatures.MIN_PERCENTAGE,
            AudioFeatures.MAX_PERCENTAGE,
        )
        tempo_min, tempo_max = self._get_audio_feature_min_and_max(
            [track.audio_features.tempo for track in tracks],
            AudioFeatures.MIN_TEMPO,
            AudioFeatures.MAX_TEMPO,
        )
        duration_ms_min, duration_ms_max = self._get_audio_feature_min_and_max(
            [track.audio_features.duration_ms for track in tracks],
            AudioFeatures.MIN_DURATION_MS,
            AudioFeatures.MAX_DURATION_MS,
        )
        return (
            AudioFeatures(
                danceability_min,
                energy_min,
                AudioFeatures.MIN_KEY_VALUE,
                loudness_min,
                AudioFeatures.MIN_MODE_VALUE,
                speechiness_min,
                acousticness_min,
                instrumentalness_min,
                liveness_min,
                valence_min,
                tempo_min,
                duration_ms_min,
                AudioFeatures.MIN_TIME_SIGNATURE,
            ),
            AudioFeatures(
                danceability_max,
                energy_max,
                AudioFeatures.MAX_KEY_VALUE,
                loudness_max,
                AudioFeatures.MAX_MODE_VALUE,
                speechiness_max,
                acousticness_max,
                instrumentalness_max,
                liveness_max,
                valence_max,
                tempo_max,
                duration_ms_max,
                AudioFeatures.MAX_TIME_SIGNATURE,
            ),
        )

    def _get_audio_feature_min_and_max(self, track_audio_features, min, max):
        lower_bound, upper_bound = self._get_middle_quantile_min_and_max(
            track_audio_features)
        lower_bound = min if not (lower_bound >= min and max <= max) else lower_bound
        upper_bound = max if not (upper_bound >= min and upper_bound <= max) else upper_bound
        return lower_bound, upper_bound

    def _get_middle_quantile_min_and_max(self, values):
        value_quantiles = quantiles(values)
        return value_quantiles[0], value_quantiles[-1]

    def _get_min_audio_features(self):
        # TODO: use AudioFeatures.MIN_*
        return AudioFeatures(
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    def _get_max_audio_features(self):
        # TODO: use AudioFeatures.MAX_*
        return AudioFeatures(
            1, 1, 11, 1, 1, 1, 1, 1, 1, 11, 300, 900000, 11)