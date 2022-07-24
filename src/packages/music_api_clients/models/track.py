from .artist import Artist


class Track:
    def __init__(self, name, artists, disc_number, duration_ms, popularity, track_number, spotify_album_id=None, spotify_id=None, spotify_uri=None, audio_features=None):
        self.name = name
        self.artists = artists
        self.disc_number = disc_number
        self.duration_ms = duration_ms
        self.popularity = popularity
        self.track_number = track_number
        self.spotify_album_id = spotify_album_id
        self.spotify_id = spotify_id
        self.spotify_uri = spotify_uri
        self.audio_features = audio_features

    def set_audio_features(self, audio_features):
        self.audio_features = audio_features

    def __key(self):
        return self.spotify_id

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Track):
            return self.__key() == other.__key()
        return NotImplemented

    def on_spotify(self):
        return self.spotify_id[:13] != "spotify:local"

    def in_any_of_albums(self, albums):
        return self.spotify_album_id in [album.spotify_id for album in albums]

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
            [
                Artist.from_spotify_track_artist(artist)
                for artist in spotify_track['artists']
            ],
            spotify_track['disc_number'],
            spotify_track['duration_ms'],
            spotify_track['popularity'],
            spotify_track['track_number'],
            spotify_album_id=spotify_track['album']['id'],
            spotify_id=spotify_track['id'],
            spotify_uri=spotify_track['uri'],
        )

    def from_spotify_album_track(spotify_track, spotify_album_id):
        return Track(
            spotify_track['name'],
            [
                Artist.from_spotify_album_track_artist(artist)
                for artist in spotify_track['artists']
            ],
            spotify_track['disc_number'],
            spotify_track['duration_ms'],
            None,
            spotify_track['track_number'],
            spotify_album_id=spotify_album_id,
            spotify_id=spotify_track['id'],
            spotify_uri=spotify_track['uri'],
        )