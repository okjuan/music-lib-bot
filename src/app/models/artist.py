class Artist:
    def __init__(self, name, id_, uri, popularity, genres, albums=None):
        """
        Params:
            name (str).
            id_ (str).
            uri (str).
            popularity (int).
            genres ([str]).
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

    def from_spotify_artist(spotify_artist):
        return Artist(
            spotify_artist['name'],
            spotify_artist['id'],
            spotify_artist['uri'],
            spotify_artist['popularity'],
            spotify_artist['genres'],
        )