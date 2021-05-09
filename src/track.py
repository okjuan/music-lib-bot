from album import Album

class Track:
    def __init__(self, name, id_, uri, album, artists, disc_number, duration_ms, popularity, track_number, date_added):
        self.name = name
        self.id = id_
        self.uri = uri
        self.album = album
        self.artists = artists
        self.disc_number = disc_number
        self.duration_ms = duration_ms
        self.popularity = popularity
        self.track_number = track_number
        self.date_added = date_added

    def from_spotify_track(spotify_track):
        """
        Params:
            spotify_track (dict): e.g. as it appears in spotify_playlist['tracks']['items'].
        """
        return Track(
            spotify_track['track']['name'],
            spotify_track['track']['id'],
            spotify_track['track']['uri'],
            Album.from_spotify_album(spotify_track['track']['album']),
            spotify_track['track']['artists'],
            spotify_track['track']['disc_number'],
            spotify_track['track']['duration_ms'],
            spotify_track['track']['popularity'],
            spotify_track['track']['track_number'],
            spotify_track['added_at'],
        )