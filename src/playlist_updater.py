from collections import defaultdict
from random import shuffle

NUM_ALBUMS_TO_FETCH = 2


class PlaylistUpdater:
    def __init__(self, playlist, my_music_lib, music_util):
        self.playlist = playlist
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.playlist_genres = None

    def duplicate_and_reduce_num_tracks_per_album(self, num_tracks_per_album, new_playlist_name):
        tracks_by_album = defaultdict(list)
        for track in self.playlist.tracks:
            tracks_by_album[track.album].append(track)

        most_popular_tracks_per_album = []
        # TODO: use music_util.get_tracks_most_popular_first(album) ?
        for album, tracks in tracks_by_album.items():
            tracks_sorted_by_popularity = sorted(
                tracks, key=lambda track: track.popularity, reverse=True)
            most_popular_tracks_per_album.extend(
                tracks_sorted_by_popularity[:num_tracks_per_album])

        print("total tracks", len(self.playlist.tracks))
        print("new set of tracks", len(most_popular_tracks_per_album))

        track_uris = [track.id for track in most_popular_tracks_per_album]
        shuffle(track_uris)
        self.my_music_lib.create_playlist(new_playlist_name, track_uris)

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

    def shuffle(self):
        pass

    def remove_all_tracks_and_add_them_back_in(self):
        """Spotify weights their shuffle play feature based on how recently a song was added. This would reweight all songs evenly"""
        pass

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