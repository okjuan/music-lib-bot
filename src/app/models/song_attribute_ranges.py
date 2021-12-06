from app.models.audio_features import AudioFeatures


class SongAttributeRanges:
    def __init__(self, danceability_range, energy_range, loudness_range, speechiness_range, acousticness_range, instrumentalness_range, liveness_range, valence_range, tempo_range, duration_ms_range, popularity_range, key_range, mode_range, time_signature_range):
        """
        Params:
            danceability_range (2-tuple of floats): (min,max), each in [0,1].
            energy_range (2-tuple of floats): (min,max), each in [0,1].
            loudness (float): decibels?
            speechiness (2-tuple of floats): (min,max), each in [0,1].
            instrumentalness (2-tuple of floats): (min,max), each in [0,1].
            acousticness (2-tuple of floats): (min,max), each in [0,1].
            liveness (2-tuple of floats): (min,max), each in [0,1].
            valence (2-tuple of floats): (min,max), each in [0,1].
            tempo (float): bpm.
            duration_ms (2-tuple of int): (min, max).
            popularity_range (2-tuple of int): (min, max), [0, 100].
            key_range (2-tuple of int): (min, max), [0, 11].
            mode_range (2-tuple of int): (min, max), 0 or 1.
            time_signature_range (2-tuple of int): (min, max), [3, 7].
        """
        self.danceability_range = danceability_range
        self.energy_range = energy_range
        self.loudness_range = loudness_range
        self.speechiness_range = speechiness_range
        self.acousticness_range = acousticness_range
        self.instrumentalness_range = instrumentalness_range
        self.liveness_range = liveness_range
        self.valence_range = valence_range
        self.tempo_range = tempo_range
        self.duration_ms_range = duration_ms_range
        self.popularity_range = (
            popularity_range
            if popularity_range is not None
            else (AudioFeatures.MIN_POPULARITY, AudioFeatures.MAX_POPULARITY)
        )
        self.key_range = (
            key_range
            if key_range is not None
            else (AudioFeatures.MIN_KEY_VALUE, AudioFeatures.MAX_KEY_VALUE)
        )
        self.mode_range = (
            mode_range
            if mode_range is not None
            else (AudioFeatures.MIN_MODE_VALUE, AudioFeatures.MAX_MODE_VALUE)
        )
        self.time_signature_range = (
            time_signature_range
            if time_signature_range is not None
            else (AudioFeatures.MIN_TIME_SIGNATURE, AudioFeatures.MAX_TIME_SIGNATURE)
        )

    def __str__(self):
        return "\n".join([
            f"Danceability: [{self.danceability_range[0]:.3f}, {self.danceability_range[1]:.3f}]",
            f"Energy: [{self.energy_range[0]:.3f}, {self.energy_range[1]:.3f}]",
            f"Loudness: [{self.loudness_range[0]:.3f}, {self.loudness_range[1]:.3f}]",
            f"Speechiness: [{self.speechiness_range[0]:.3f}, {self.speechiness_range[1]:.3f}]",
            f"Acousticness: [{self.acousticness_range[0]:.3f}, {self.acousticness_range[1]:.3f}]",
            f"Instrumentalness: [{self.instrumentalness_range[0]:.3f}, {self.instrumentalness_range[1]:.3f}]",
            f"Liveness: [{self.liveness_range[0]:.3f}, {self.liveness_range[1]:.3f}]",
            f"Valence: [{self.valence_range[0]:.3f}, {self.valence_range[1]:.3f}]",
            f"Tempo: [{self.tempo_range[0]:.3f}, {self.tempo_range[1]:.3f}]",
            f"Duration in ms: [{self._in_min_sec_format(self.duration_ms_range[0])}, {self._in_min_sec_format(self.duration_ms_range[1])}]",
            f"Popularity: [{self.popularity_range[0]}, {self.popularity_range[1]}]",
            f"Key: [{self.key_range[0]}, {self.key_range[1]}]",
            f"Mode: [{self.mode_range[0]}, {self.mode_range[1]}]",
            f"Time Signature: [{self.time_signature_range[0]}, {self.time_signature_range[1]}]",
        ])

    def _in_min_sec_format(self, milliseconds):
        "Given a (float) milliseconds, returns (str) e.g. '3min20'."
        seconds = int(milliseconds / 1000)
        full_minutes = seconds // 60
        remaining_seconds = seconds % 6
        return f"{full_minutes}min{remaining_seconds}"

    def set_popularity_min_max_range(self, popularity_min, popularity_max):
        self.popularity_range = (popularity_min, popularity_max)

    def from_audio_features_min_max_ranges(audio_features_min, audio_features_max):
        """Defaults to accepting all keys, modes, and time_signatures since these field are
        less important right now. Also defaults to accepting all popularity values,
        but you can modify that by calling SongAttributeRanges.set_popularity_min_max_range.
        Of course you can also set key_range, mode_range, and time_signature_range directly.
        """
        return SongAttributeRanges(
            (audio_features_min.danceability, audio_features_max.danceability),
            (audio_features_min.energy, audio_features_max.energy),
            (audio_features_min.loudness, audio_features_max.loudness),
            (audio_features_min.speechiness, audio_features_max.speechiness),
            (audio_features_min.acousticness, audio_features_max.acousticness),
            (audio_features_min.instrumentalness, audio_features_max.instrumentalness),
            (audio_features_min.liveness, audio_features_max.liveness),
            (audio_features_min.valence, audio_features_max.valence),
            (audio_features_min.tempo, audio_features_max.tempo),
            (audio_features_min.duration_ms, audio_features_max.duration_ms),
            popularity_range = None,
            key_range = None,
            mode_range = None,
            time_signature_range = None,
        )