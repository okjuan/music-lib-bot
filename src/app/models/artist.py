class Artist:
    def __init__(self, name, id_, uri, popularity=None, genres=None, albums=None):
        """
        Params:
            name (str).
            id_ (str).
            uri (str).
            popularity (int|None) in range [0, 100], optional.
            genres ([str]|None), optional.
            albums ([Album]).
        """
        self.name = name
        self.id = id_
        self.uri = uri
        self.popularity = popularity
        self.genres = genres
        self.albums = albums

    def __key(self):
        return self.id

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Artist):
            return self.__key() == other.__key()
        return NotImplemented

    def set_albums(self, albums):
        self.albums = albums

    def set_genres(self, genres):
        self.genres = genres

    def from_spotify_artist(spotify_artist):
        return Artist(
            spotify_artist['name'],
            spotify_artist['id'],
            spotify_artist['uri'],
            popularity=spotify_artist['popularity'],
            genres=spotify_artist['genres'],
        )

    def from_spotify_track_artist(spotify_artist):
        return Artist(
            spotify_artist['name'],
            spotify_artist['id'],
            spotify_artist['uri'],
        )

    def from_spotify_album_track_artist(spotify_artist):
        return Artist(
            spotify_artist['name'],
            spotify_artist['id'],
            spotify_artist['uri'],
        )

    def from_spotify_album_artist(spotify_artist):
        return Artist(
            spotify_artist['name'],
            spotify_artist['id'],
            spotify_artist['uri'],
        )