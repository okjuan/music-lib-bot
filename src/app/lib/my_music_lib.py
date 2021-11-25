from random import randint


# To prevent fetching a copious amount of albums and overwhelming memory
MAX_ALBUMS_TO_FETCH = 1000


class MyMusicLib:
    def __init__(self, spotify_client_wrapper, music_util, info_logger):
        self.spotify_client_wrapper = spotify_client_wrapper
        self.music_util = music_util
        self.info_logger = info_logger

    def get_playlist_by_name(self, name):
        return self.spotify_client_wrapper.get_current_user_playlist_by_name(name)

    def get_playlist_by_id(self, playlist_id):
        return self.spotify_client_wrapper.get_playlist(playlist_id)

    def create_playlist(self, name, track_uris, description=""):
        playlist = self.spotify_client_wrapper.create_playlist(name, description)
        self.spotify_client_wrapper.add_tracks(playlist.id, track_uris)
        return playlist

    def get_my_albums_grouped_by_genre(self, albums_to_fetch, min_genres_per_group):
        """
        Returns:
            albums_by_genre ([dict]):
                e.g. [{genres: ['rock', 'dance rock'], albums: [Album]}]
        """
        albums = self.spotify_client_wrapper.get_my_albums(albums_to_fetch)
        if len(albums) == 0:
            return []

        self.info_logger(f"Grouping {len(albums)} albums...")
        albums_by_genre = self.music_util.group_albums_by_genre(albums, min_genres_per_group)

        self.info_logger(f"Matched into {len(albums_by_genre)} groups...")
        return albums_by_genre

    def get_all_my_albums_grouped_by_genre(self, min_genres_per_group):
        """
        Returns:
            albums_by_genre ([dict]):
                e.g. [{genres: ['rock', 'dance rock'], albums: [Album]}]
        """
        return self.get_my_albums_grouped_by_genre(MAX_ALBUMS_TO_FETCH, min_genres_per_group)

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        self.spotify_client_wrapper.add_tracks(playlist_id, track_uris)

    def add_track_to_playlist_at_position(self, playlist_id, track_uri, position):
        self.spotify_client_wrapper.add_track_at_position(playlist_id, track_uri, position)

    def add_tracks_in_random_positions(self, playlist, track_uris):
        if len(track_uris) == 0:
            self.info_logger("Oops, no tracks given, so I can't add them to your playlist.")
        self.info_logger(f"Adding {len(track_uris)} randomly throughout your playlist: '{playlist.name}'")
        for track in track_uris:
            random_position = randint(1, len(playlist.tracks)) if len(playlist.tracks) > 0 else 1
            self.add_track_to_playlist_at_position(
                playlist.id, track, random_position)