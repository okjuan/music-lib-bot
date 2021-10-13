from app.models.album import Album
from app.models.playlist import Playlist
from app.models.track import Track

def mock_album(id="", genres=[], artists=[], name=""):
    return Album(name, id, [], artists, release_date="", num_tracks=0, genres=genres)

def mock_track():
    return Track("", "", "", mock_album(), [mock_artist], 0)

def mock_artist(id="", name=""):
    return dict(id=id, name=name)