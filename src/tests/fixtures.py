from app.models.album import Album
from app.models.artist import Artist
from app.models.audio_features import AudioFeatures
from app.models.playlist import Playlist
from app.models.track import Track
from app.models.song_attribute_ranges import SongAttributeRanges

def mock_album(id="", genres=[], artists=[], name=""):
    return Album(name, id, [], artists, release_date="", num_tracks=0, genres=genres)

def mock_artist(name="", id="", uri="", popularity=0, genres=[], albums=None):
    return Artist(name, id, uri, popularity, genres, albums)

def mock_track(name="", id_="", uri="", album=mock_album(), artists=[mock_artist()], disc_number=1, duration_ms=0, popularity=0, track_number=1, audio_features=None):
    audio_features = mock_audio_features() if audio_features is None else audio_features
    return Track(
        name,
        id_,
        uri,
        album.id,
        artists,
        disc_number,
        duration_ms,
        popularity,
        track_number,
        audio_features,
    )

def mock_playlist(id_="", name="", description="", tracks=[]):
    return Playlist(id_, name, description, lambda: tracks)

def mock_song_attribute_ranges(danceability_range=[0,1], energy_range=[0,1], loudness_range=[0,1], speechiness_range=[0,1], acousticness_range=[0,1], instrumentalness_range=[0,1], liveness_range=[0,1], valence_range=[0,1], tempo_range=[0,300], duration_ms_range=[0,900000], popularity_range=[0,100], key_range=[0,11], mode_range=[0,1], time_signature_range=[0,11]):
    return SongAttributeRanges(
        danceability_range,
        energy_range,
        loudness_range,
        speechiness_range,
        acousticness_range,
        instrumentalness_range,
        liveness_range,
        valence_range,
        tempo_range,
        duration_ms_range,
        popularity_range,
        key_range,
        mode_range,
        time_signature_range
    )

def mock_audio_features(danceability=1, energy=1, loudness=1, speechiness=1, acousticness=1, instrumentalness=1, liveness=1, valence=1, tempo=0, duration_ms=0, popularity=0, key=0, mode=1, time_signature=0):
    return AudioFeatures(
        danceability,
        energy,
        loudness,
        speechiness,
        acousticness,
        instrumentalness,
        liveness,
        valence,
        tempo,
        duration_ms,
        key,
        mode,
        time_signature
    )