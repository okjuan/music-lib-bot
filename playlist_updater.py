from random import shuffle

NUM_ALBUMS_TO_FETCH = 2


class PlaylistUpdater:
    def __init__(self, playlist, my_music_lib, music_util):
        self.playlist = playlist
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.playlist_genres = None

    def add_tracks_from_my_saved_albums_with_same_genres(self, num_tracks_per_album):
        track_uris = self._get_tracks_from_my_saved_albums_with_same_genres(
            num_tracks_per_album)
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

    def _get_tracks_from_my_saved_albums_with_same_genres(self, num_tracks_per_album):
        """Skips albums that are already present in the playlist."""
        genres = self._get_playlist_genres()
        if len(genres) == 0:
            print("Couldn't find any genres :(")
            return []
        print(f"Your playlist's genres are {', '.join(genres)}")

        albums_in_playlist = [
            album.id
            for album in self.music_util.get_albums(self.playlist.tracks)
        ]
        return [
            track['uri']
            for album in self._get_my_albums_with_same_genres(genres)
            if album['id'] not in albums_in_playlist
            for track in self.music_util.get_most_popular_tracks(album, num_tracks_per_album)
        ]

    def _get_playlist_genres(self):
        if self.playlist_genres is None:
            target_genres = self.music_util.get_genres_in_playlist(self.playlist.id)
            self.playlist_genres = [] if len(target_genres) == 0 else target_genres
        return self.playlist_genres

    def _get_my_albums_with_same_genres(self, genres):
        album_groups = self.my_music_lib.get_my_albums_grouped_by_genre(
            NUM_ALBUMS_TO_FETCH, len(genres))
        sorted_genres = sorted(genres)
        for group in album_groups:
            if sorted_genres == sorted(group['genres']):
                print(f"Good news! I found {len(group['albums'])} album(s) matching your playlist's genres:")
                print(self.music_util.get_albums_as_readable_list(group['albums']))
                return group['albums']
        print("Sorry, I couldn't find any albums matching your playlist's genres :(")
        return []