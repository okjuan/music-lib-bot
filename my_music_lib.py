from spotify_client_wrapper import SpotifyClientWrapper


class MyMusicLib:
    def __init__(self):
        self.spotify_client = SpotifyClientWrapper()

    def get_playlist(self, name):
        return self.spotify_client.get_current_user_playlist(name)

    def get_my_albums_by_genres(self, genres):
        return None