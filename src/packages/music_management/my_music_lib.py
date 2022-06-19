from random import randint, shuffle


# To prevent fetching a copious amount of albums and overwhelming memory
MAX_ALBUMS_TO_FETCH = 1000


class MyMusicLib:
    def __init__(self, music_api_client, music_util, info_logger):
        self.music_api_client = music_api_client
        self.music_util = music_util
        self.info_logger = info_logger

    def get_playlist_by_name(self, name):
        return self.music_api_client.get_current_user_playlist_by_name(name)

    def search_my_playlists(self, keyword):
        return self.music_api_client.find_current_user_matching_playlists(keyword)

    def get_playlist_by_id(self, playlist_id):
        return self.music_api_client.get_playlist(playlist_id)

    def create_playlist(self, name, track_uris, description=""):
        playlist = self.music_api_client.create_playlist(name, description)
        if len(track_uris) > 0:
            self.music_api_client.add_tracks(playlist.id, track_uris)
        return playlist

    def get_or_create_playlist(self, name):
        playlist = self.get_playlist_by_name(name)
        if playlist is None:
            playlist = self.create_playlist(name, [])
        return playlist

    def get_my_albums_grouped_by_genre(self, albums_to_fetch, min_genres_per_group):
        """
        Returns:
            albums_by_genre ([dict]):
                e.g. [{genres: ['rock', 'dance rock'], albums: [Album]}]
        """
        albums = self.music_api_client.get_my_albums(albums_to_fetch)
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
        self.music_api_client.add_tracks(playlist_id, track_uris)

    def add_track_to_playlist_at_position(self, playlist_id, track_uri, position):
        self.music_api_client.add_track_at_position(playlist_id, track_uri, position)

    def add_tracks_in_random_positions(self, playlist, track_uris):
        if len(track_uris) == 0:
            self.info_logger("Oops, no tracks given, so I can't add them to your playlist.")
            return

        self.info_logger(f"Adding {len(track_uris)} randomly throughout your playlist: '{playlist.name}'")
        if playlist.get_num_tracks() == 0:
            shuffled_track_uris = track_uris[:]
            shuffle(shuffled_track_uris)
            self.add_tracks_to_playlist(playlist.id, shuffled_track_uris)
        else:
            num_tracks_in_playlist = playlist.get_num_tracks()
            for track in track_uris:
                random_position = randint(1, num_tracks_in_playlist)
                self.add_track_to_playlist_at_position(
                    playlist.id, track, random_position)
                num_tracks_in_playlist += 1

    def remove_tracks_from_playlist(self, playlist, track_uris):
        self.music_api_client.remove_tracks_from_playlist(
            playlist.id, track_uris)