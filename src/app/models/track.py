from app.models.artist import Artist


class Track:
    def __init__(self, name, id_, uri, album_id, artists, disc_number, duration_ms, popularity, track_number, audio_features=None):
        self.name = name
        self.id = id_
        self.uri = uri
        self.album_id = album_id
        self.artists = artists
        self.disc_number = disc_number
        self.duration_ms = duration_ms
        self.popularity = popularity
        self.track_number = track_number
        self.audio_features = audio_features

    def set_audio_features(self, audio_features):
        self.audio_features = audio_features

    def __key(self):
        return self.id

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Track):
            return self.__key() == other.__key()
        return NotImplemented

    def from_spotify_playlist_track(spotify_playlist_track):
        """
        Params:
            spotify_playlist_track (dict): e.g. as it appears in spotify_playlist['tracks']['items'].
        """
        return Track.from_spotify_track(spotify_playlist_track['track'])

    def from_spotify_track(spotify_track):
        """
        Params:
            spotify_track (dict).
        """
        return Track(
            spotify_track['name'],
            spotify_track['id'],
            spotify_track['uri'],
            spotify_track['album']['id'],
            [
                Artist.from_spotify_track_artist(artist)
                for artist in spotify_track['artists']
            ],
            spotify_track['disc_number'],
            spotify_track['duration_ms'],
            spotify_track['popularity'],
            spotify_track['track_number'],
        )

    def from_spotify_album_track(spotify_track, album_id):
        return Track(
            spotify_track['name'],
            spotify_track['id'],
            spotify_track['uri'],
            album_id,
            [
                Artist.from_spotify_album_track_artist(artist)
                for artist in spotify_track['artists']
            ],
            spotify_track['disc_number'],
            spotify_track['duration_ms'],
            None,
            spotify_track['track_number'],
        )