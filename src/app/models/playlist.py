from app.models.track import Track

class Playlist:
    def __init__(self, id_, name, description, tracks_fetcher):
        self.id = id_
        self.name = name
        self.description = description
        self.tracks_fetcher = tracks_fetcher
        self.tracks = None
        self.num_tracks = None

    def get_tracks(self):
        if self.tracks is None:
            self.tracks = self.tracks_fetcher()
        return self.tracks

    def get_num_tracks(self):
        if self.num_tracks is None:
            if self.tracks is None:
                self.tracks = self.tracks_fetcher()
            self.num_tracks = len(self.tracks)
        return self.num_tracks

    def from_spotify_playlist(spotify_playlist):
        return Playlist(
            spotify_playlist['id'],
            spotify_playlist['name'],
            spotify_playlist['description'],
            lambda: [
                Track.from_spotify_playlist_track(track)
                for track in spotify_playlist['tracks']['items']
            ],
        )