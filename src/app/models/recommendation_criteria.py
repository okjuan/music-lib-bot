class RecommendationCriteria:
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
        self.popularity_range = popularity_range
        self.key_range = key_range
        self.mode_range = mode_range
        self.time_signature_range = time_signature_range

    def set_popularity_min_max_range(self, popularity_min, popularity_max):
        self.popularity_range = (popularity_min, popularity_max)

    def from_audio_features_min_max_ranges(audio_features_min, audio_features_max):
        """Defaults to accepting all keys, modes, and time_signatures since these field are
        less important right now. Also defaults to accepting all popularity values,
        but that can be modified by calling RecommendationCriteria.set_popularity_min_max_range.
        """
        return RecommendationCriteria(
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