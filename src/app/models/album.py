from app.models.track import Track
from datetime import datetime


class Album:
    def __init__(self, name, id_, tracks, artists, release_date, num_tracks, genres=None):
        """
        Params:
            name (str).
            id (str).
            artists ([dict]).
            release_date (str): in ISO format e.g. '1967-03-12'
            num_tracks (int).
        """
        self.name = name
        self.id = id_
        self.tracks = tracks
        self.artists = artists
        self.release_date = self._parse_date(release_date)
        self.num_tracks = num_tracks
        self.genres = genres

    def _parse_date(self, spotify_release_date):
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

    def from_spotify_album(spotify_album):
        return Album(
            spotify_album['name'],
            spotify_album['id'],
            [
                Track.from_spotify_album_track(track, spotify_album['id'])
                for track in spotify_album['tracks']['items']
            ],
            spotify_album['artists'],
            spotify_album['release_date'],
            spotify_album['total_tracks'],
        )