# NOTES:
# Assumes existence of:
# - [ ] Playlist object
#   - with __contains__ implementation
#   - with methods
# - [ ] music_recommender API
# - [x] music_util API
# - [x] MyMusicLib API object


import music_recommender
import music_util
from my_music_lib import MyMusicLib

class PlaylistUpdater:
    def __init__(self, playlist, my_music_lib):
        self.playlist = playlist
        self.my_music_lib = my_music_lib

    def add_new_tracks_from_saved_albums(self):
        tracks_to_add = [
            track
            for album in self.get_my_albums_that_suit_this_playlist(self.playlist)
            # requires custom implementation of __contains__
            if album in self.playlist
            for track in music_util.get_most_popular_tracks(album, 3)
        ]

    def get_my_albums_that_suit_this_playlist(self):
        genres = self.playlist.get_description()
        return self.my_music_lib.get_all_my_albums_grouped_by_genre(genres)

    def add_new_tracks_from_recommendations(self):
        tracks_to_add = [
            track
            for recommended_album in music_recommender.get_recommendations(playlist_name)
            # requires custom implementation of __contains__
            if recommended_album in self.playlist
            for track in music_util.get_most_popular_tracks(recommended_album, 3)
        ]

def main():
    my_music_lib = MyMusicLib()
    playlist = my_music_lib.get_playlist("PlaylistUpdater Test Playlist")
    playlist_updater = PlaylistUpdater(playlist, my_music_lib)
    playlist_updater.add_new_tracks_from_saved_albums()


if __name__ == "__main__":
    main()