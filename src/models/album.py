class Album:
    def __init__(self, name, id_, artists, release_date, num_tracks):
        """
        Params:
            name (str).
            id (str).
            artists ([dict]).
            release_date (str): e.g. '1967-03-12'
            num_tracks (int).
        """
        self.name = name
        self.id = id_
        self.artists = artists
        self.release_date = release_date
        self.num_tracks = num_tracks
        self.genres = None

    def __key(self):
        return self.id

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Album):
            return self.__key() == other.__key()
        return NotImplemented

    def set_genres(self, genres):
        self.genres = genres

    def from_spotify_album(spotify_album):
        return Album(
            spotify_album['name'],
            spotify_album['id'],
            spotify_album['artists'],
            spotify_album['release_date'],
            spotify_album['total_tracks'],
        )