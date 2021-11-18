class PlaylistStats:
    def __init__(self, my_music_lib, music_util, info_logger):
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.info_logger = info_logger

    def get_playlist_with_track_audio_features(self, playlist_name):
        """
        Params:
            playlist_name (str).

        Returns:
            playlist (Playlist): with tracks that have audio_features populated.
        """
        playlist = self.my_music_lib.get_playlist_by_name(playlist_name)
        self.music_util.populate_track_audio_features(playlist)
        return playlist