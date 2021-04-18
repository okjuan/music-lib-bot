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
                Playlist.from_spotify_track(track)
                for track in spotify_playlist['tracks']['items']
            ],
        )

    def from_spotify_track(spotify_track):
        return {
            'added_at': spotify_track['added_at'],
            **spotify_track['track']
        }