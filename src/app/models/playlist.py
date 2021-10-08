from app.models.track import Track

class Playlist:
    def __init__(self, id_, name, description, tracks):
        self.id = id_
        self.name = name
        self.description = description
        self.tracks = tracks

    def from_spotify_playlist(spotify_playlist):
        return Playlist(
            spotify_playlist['id'],
            spotify_playlist['name'],
            spotify_playlist['description'],
            [
                Track.from_spotify_playlist_track(track)
                for track in spotify_playlist['tracks']['items']
            ],
        )