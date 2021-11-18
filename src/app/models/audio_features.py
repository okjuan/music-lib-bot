class AudioFeatures:
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