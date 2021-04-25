from music_util import MusicUtil
from my_music_lib import MyMusicLib
from playlist import Playlist
from random import shuffle
from spotify_client_wrapper import SpotifyClientWrapper

NUM_ALBUMS_TO_FETCH = 30

class PlaylistUpdater:
    def __init__(self, playlist, my_music_lib, music_util):
        self.playlist = playlist
        self.my_music_lib = my_music_lib
        self.music_util = music_util

    def add_new_tracks_from_saved_albums(self):
        track_uris = self.get_tracks_to_add()
        if len(track_uris) == 0:
            print(f"No tracks to add to your playlist: '{self.playlist.name}'")
            return

        print(f"Found {len(track_uris)} tracks to add to playlist...")
        shuffle(track_uris)
        if len(track_uris) > 0:
            print(f"Adding them to your playlist: '{self.playlist.name}'")
            self.my_music_lib.add_tracks_to_playlist(self.playlist.id, track_uris)
        else:
            print("Not adding any songs to your playlist.")

    def get_tracks_to_add(self):
        genres = self.get_playlist_genres()
        albums_in_playlist = [
            album.id
            for album in self.music_util.get_albums(self.playlist.tracks)
        ]
        return [
            track['uri']
            for album in self.get_my_albums(genres)
            if album['id'] not in albums_in_playlist
            for track in self.music_util.get_most_popular_tracks(album, 3)
        ]

    def get_playlist_genres(self):
        target_genres = self.music_util.get_genres_in_playlist(self.playlist.id)
        if len(target_genres) == 0:
            print("Couldn't find any genres :(")
            return []
        print(f"Your playlist's genres are {', '.join(target_genres)}")
        return target_genres

    def get_my_albums(self, target_genres):
        album_groups = self.my_music_lib.get_all_my_albums_grouped_by_genre(len(target_genres))
        for group in album_groups:
            if sorted(target_genres) == sorted(group['genres']):
                print(f"Good news! I found {len(group['albums'])} album(s) matching your playlist's genres:")
                print(self.music_util.get_albums_as_readable_list(group['albums']))
                return group['albums']
        print("Sorry, I couldn't find any albums matching your playlist's genres :(")
        return []

def main():
    spotify_client_wrapper = SpotifyClientWrapper()
    music_util = MusicUtil(spotify_client_wrapper)
    my_music_lib = MyMusicLib(spotify_client_wrapper, music_util)

    playlist_name = "PlaylistUpdater Test Playlist"
    playlist = my_music_lib.get_playlist(playlist_name)
    if playlist is None:
        print(f"Couldn't find your playlist '{playlist_name}'")
        return

    playlist_updater = PlaylistUpdater(playlist, my_music_lib, music_util)
    playlist_updater.add_new_tracks_from_saved_albums()


if __name__ == "__main__":
    main()