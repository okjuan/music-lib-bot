import os

from collections import namedtuple
from unittest.mock import Mock


mock_spotify_artist_factory = namedtuple("MockSpotifyArtist", ['name'])

mock_spotify_track_factory = namedtuple(
    "MockSpotifyTrack", ['name', 'uri', 'artists', 'popularity', 'album'])

mock_spotify_album_factory = namedtuple(
    "MockSpotifyAlbum", ['name', 'uri', 'artists', 'songs', 'popularity'])

def get_path_to_test_input_file(name):
    # Relative from repo root
    return os.path.abspath(f"tests/test_inputs/{name}")

def get_num_times_called(mock):
    if isinstance(mock, Mock):
        return len(mock.call_args_list)
    return NotImplemented