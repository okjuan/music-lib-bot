class Track:
    def __init__(self, name, id_, uri, album_id, artists, disc_number, duration_ms, popularity, track_number):
        self.name = name
        self.id = id_
        self.uri = uri
        self.album_id = album_id
        self.artists = artists
        self.disc_number = disc_number
        self.duration_ms = duration_ms
        self.popularity = popularity
        self.track_number = track_number

    def from_spotify_playlist_track(spotify_playlist_track):
        """
        Params:
            spotify_playlist_track (dict): e.g. as it appears in spotify_playlist['tracks']['items'].
        """
        return Track.from_spotify_track(spotify_playlist_track['track'])

    def from_spotify_track(spotify_track):
        """
        Params:
            spotify_track (dict).
        """
        return Track(
            spotify_track['name'],
            spotify_track['id'],
            spotify_track['uri'],
            spotify_track['album']['id'],
            spotify_track['artists'],
            spotify_track['disc_number'],
            spotify_track['duration_ms'],
            spotify_track['popularity'],
            spotify_track['track_number'],
        )

    def from_spotify_album_track(spotify_track, album_id):
        return Track(
            spotify_track['name'],
            spotify_track['id'],
            spotify_track['uri'],
            album_id,
            spotify_track['artists'],
            spotify_track['disc_number'],
            spotify_track['duration_ms'],
            None,
            spotify_track['track_number'],
        )