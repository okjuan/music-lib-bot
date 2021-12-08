class AudioFeatures:
    MIN_KEY_VALUE, MAX_KEY_VALUE = 0, 11
    MIN_MODE_VALUE, MAX_MODE_VALUE = 0, 1
    MIN_TIME_SIGNATURE, MAX_TIME_SIGNATURE = 0, 11
    MIN_TEMPO, MAX_TEMPO = 0, 500
    MIN_DURATION_MS, MAX_DURATION_MS = 0, 900000
    MIN_LOUDNESS, MAX_LOUDNESS = -60, 0
    MIN_PERCENTAGE, MAX_PERCENTAGE = 0, 1
    MIN_POPULARITY, MAX_POPULARITY = 0, 100
    MIN_DANCEABILITY = MIN_ENERGY = MIN_SPEECHINESS = MIN_ACOUSTICNESS = MIN_PERCENTAGE
    MIN_INSTRUMENTALNESS = MIN_LIVENESS = MIN_VALENCE = MIN_PERCENTAGE
    MAX_DANCEABILITY = MAX_ENERGY = MAX_SPEECHINESS = MAX_ACOUSTICNESS = MAX_PERCENTAGE
    MAX_INSTRUMENTALNESS = MAX_LIVENESS = MAX_VALENCE = MAX_PERCENTAGE

    def __init__(self, danceability, energy, key, loudness, mode, speechiness, acousticness, instrumentalness, liveness, valence, tempo, duration_ms, time_signature):
        """
        Params:
            danceability (float): [0,1]
            energy (float): [0,1]
            key (int).
            loudness (float): decibels?
            mode (int).
            speechiness (float): [0,1]
            instrumentalness (float): [0,1]
            acousticness (float): [0,1]
            liveness (float): [0,1]
            valence (float): [0,1]
            tempo (float): bpm.
            duration_ms (int).
            time_signature (int).
        """
        self.danceability = danceability
        self.energy = energy
        self.key = key
        self.loudness = loudness
        self.mode = mode
        self.speechiness = speechiness
        self.acousticness = acousticness
        self.instrumentalness = instrumentalness
        self.liveness = liveness
        self.valence = valence
        self.tempo = tempo
        self.duration_ms = duration_ms
        self.time_signature = time_signature

    def from_spotify_audio_features(spotify_audio_features):
        return AudioFeatures(
            spotify_audio_features["danceability"],
            spotify_audio_features["energy"],
            spotify_audio_features["key"],
            spotify_audio_features["loudness"],
            spotify_audio_features["mode"],
            spotify_audio_features["speechiness"],
            spotify_audio_features["acousticness"],
            spotify_audio_features["instrumentalness"],
            spotify_audio_features["liveness"],
            spotify_audio_features["valence"],
            spotify_audio_features["tempo"],
            spotify_audio_features["duration_ms"],
            spotify_audio_features["time_signature"],
        )

    def with_minimum_values():
        return AudioFeatures(
            AudioFeatures.MIN_DANCEABILITY,
            AudioFeatures.MIN_ENERGY,
            AudioFeatures.MIN_KEY_VALUE,
            AudioFeatures.MIN_LOUDNESS,
            AudioFeatures.MIN_MODE_VALUE,
            AudioFeatures.MIN_SPEECHINESS,
            AudioFeatures.MIN_ACOUSTICNESS,
            AudioFeatures.MIN_INSTRUMENTALNESS,
            AudioFeatures.MIN_LIVENESS,
            AudioFeatures.MIN_VALENCE,
            AudioFeatures.MIN_TEMPO,
            AudioFeatures.MIN_DURATION_MS,
            AudioFeatures.MIN_TIME_SIGNATURE,
        )

    def with_maximum_values():
        return AudioFeatures(
            AudioFeatures.MAX_DANCEABILITY,
            AudioFeatures.MAX_ENERGY,
            AudioFeatures.MAX_KEY_VALUE,
            AudioFeatures.MAX_LOUDNESS,
            AudioFeatures.MAX_MODE_VALUE,
            AudioFeatures.MAX_SPEECHINESS,
            AudioFeatures.MAX_ACOUSTICNESS,
            AudioFeatures.MAX_INSTRUMENTALNESS,
            AudioFeatures.MAX_LIVENESS,
            AudioFeatures.MAX_VALENCE,
            AudioFeatures.MAX_TEMPO,
            AudioFeatures.MAX_DURATION_MS,
            AudioFeatures.MAX_TIME_SIGNATURE,
        )