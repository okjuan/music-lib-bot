from app.models.track import Track
from app.models.artist import Artist
from datetime import datetime


class Album:
    def __init__(self, name, id_, tracks, artists, release_date, num_tracks, genres=None, popularity=None):
        """
        Params:
            name (str).
            id (str).
            artists ([dict]).
            release_date (datetime).
            num_tracks (int).
            genres ([str]), optional.
            popularity (int) in range [0, 100], optional.
        """
        self.name = name
        self.id = id_
        self.tracks = tracks
        self.artists = artists
        self.release_date = release_date
        self.num_tracks = num_tracks
        self.genres = genres
        self.popularity = popularity

    def _parse_date(spotify_release_date):
        """For Herbie Hancock alone, I've seen these release_dates:
        - "1999-01-01"
        - "2009"
        - "1980-03"
        """
        # sometime Spotify just gives a year
        if len(spotify_release_date) == 4:
            # default to first day of year
            return datetime.fromisocalendar(int(spotify_release_date), 1, 1)
        elif len(spotify_release_date) == 7:
            # default to first day of month
            return datetime.fromisocalendar(
                int(spotify_release_date[:4]), int(spotify_release_date[5:7]), 1)
        else:
            return datetime.fromisoformat(spotify_release_date)

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

    def set_popularity(self, popularity):
        self.popularity = popularity

    def from_spotify_album(spotify_album):
        return Album(
            spotify_album['name'],
            spotify_album['id'],
            [
                Track.from_spotify_album_track(track, spotify_album['id'])
                for track in spotify_album['tracks']['items']
            ],
            [
                Artist.from_spotify_album_artist(artist)
                for artist in spotify_album['artists']
            ],
            Album._parse_date(spotify_album['release_date']),
            spotify_album['total_tracks'],
            popularity=spotify_album['popularity'],
        )