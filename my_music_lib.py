from spotify_client_wrapper import SpotifyClientWrapper
from music_util import MusicUtil

# To prevent fetching a copious amount of albums and overwhelming memory
MAX_ALBUMS_TO_FETCH = 1000


class MyMusicLib:
    def __init__(self):
        self.spotify_client_wrapper = SpotifyClientWrapper()
        self.music_util = MusicUtil(self.spotify_client_wrapper)

    def get_playlist(self, name):
        return self.spotify_client_wrapper.get_current_user_playlist(name)

    def get_my_albums_grouped_by_genre(self, albums_to_fetch, min_genres_per_group):
        """
        Returns:
            albums_by_genre (dict): key:string, value:[Album].
                e.g. {'rock': [Album], 'jazz': [Album, Album]}.
        """
        albums = self.spotify_client_wrapper.get_my_albums(albums_to_fetch)
        if len(albums) == 0:
            return {}

        print(f"Grouping {len(albums)} albums...")
        albums_by_genre = self.music_util.group_albums_by_genre(albums, min_genres_per_group)

        print(f"Matched into {len(albums_by_genre)} groups...")
        return albums_by_genre

    def get_all_my_albums_grouped_by_genre(self, min_genres_per_group):
        """
        Returns:
            albums_by_genre (dict): key:string, value:[Album].
                e.g. {'rock': [Album], 'jazz': [Album, Album]}.
        """
        return self.get_my_albums_grouped_by_genre(MAX_ALBUMS_TO_FETCH, min_genres_per_group)