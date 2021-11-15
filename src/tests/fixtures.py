from app.models.album import Album
from app.models.artist import Artist
from app.models.playlist import Playlist
from app.models.track import Track

def mock_album(id="", genres=[], artists=[], name=""):
    return Album(name, id, [], artists, release_date="", num_tracks=0, genres=genres)

def mock_artist(name="", id="", uri="", popularity=0, genres=[], albums=None):
    return Artist(name, id, uri, popularity, genres, albums)

def mock_track(name="", id_="", uri="", album=mock_album(), artists=[mock_artist()], disc_number=1, duration_ms=0, popularity=0, track_number=1):
    return Track(
        name,
        id,
        uri,
        album.id,
        artists,
        disc_number,
        duration_ms,
        popularity,
        track_number,
    )

def mock_playlist(id_="", name="", description="", tracks=[]):
    return Playlist(id_, name, description, tracks)