from packages.music_api_clients.models.track import Track

class Playlist:
    def __init__(self, name, description, tracks_fetcher, spotify_id=None):
        self.name = name
        self.description = description
        self.tracks_fetcher = tracks_fetcher
        self.spotify_id = spotify_id
        self.tracks = None
        self.num_tracks = None

    def __key(self):
        return self.spotify_id

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Playlist):
            return self.__key() == other.__key()
        return NotImplemented

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

    def has_any_tracks_from_album(self, album):
        for track in self.get_tracks():
            if album.contains_track(track):
                return True
        return False

    def from_spotify_playlist(spotify_playlist):
        return Playlist(
            spotify_playlist['name'],
            spotify_playlist['description'],
            lambda: [
                Track.from_spotify_playlist_track(track)
                for track in spotify_playlist['tracks']['items']
            ],
            spotify_id=spotify_playlist['id'],
        )

    def from_spotify_playlist_search_results(spotify_playlist, tracks_fetcher):
        playlist = Playlist(
            spotify_playlist['name'],
            spotify_playlist['description'],
            tracks_fetcher,
            spotify_id=spotify_playlist['id'],
        )
        return playlist