from collections import defaultdict
from random import shuffle


class PlaylistCreator:
    def __init__(self, spotify_client, my_music_lib, music_util, info_logger):
        self.spotify_client = spotify_client
        self.my_music_lib = my_music_lib
        self.music_util = music_util
        self.info_logger = info_logger

    def create_playlist_from_albums(self, album_group, get_num_tracks_per_album):
        tracks = self.music_util.get_most_popular_tracks_from_each(
            album_group["albums"], get_num_tracks_per_album())
        shuffle(tracks)

        self.info_logger(f"Creating '{album_group['description']}' playlist from {len(album_group['albums'])} albums...")
        self.my_music_lib.create_playlist(
            album_group["description"],
            [track.uri for track in tracks],
            description="created by playlist_creator"
        )
        self.info_logger(f"Playlist created!")

    def create_playlist_based_on_existing_playlist(self, get_playlist, get_new_playlist_name, get_num_tracks_per_album):
        self.duplicate_and_reduce_num_tracks_per_album(
            get_playlist, get_new_playlist_name, get_num_tracks_per_album)

    def _get_discography(self, get_artist):
        artist = get_artist()
        if artist is None:
            return None
        albums = self.music_util.get_discography(artist)
        if albums is None or albums == []:
            return None
        return albums

    # TODO: should I be reusing/reappropriating create_playlist_from_albums()?
    # TODO: break down this function. It's too long!
    def create_playlist_from_an_artists_discography(self, get_artist, get_num_tracks_per_album, get_new_playlist_name):
        albums = self._get_discography(get_artist)
        if albums is None:
            return

        self.info_logger(f"Out of the total {len(albums)} number of albums...")
        albums = self.music_util.filter_out_duplicates_demos_and_live_albums(albums)
        self.info_logger(f"Only {len(albums)} are essential; the rest are duplicates, demos, and live albums.")

        albums = self.music_util.order_albums_chronologically(albums)

        # NOTE: do list comprehension here to ensure album order is preserved
        num_tracks_per_album = get_num_tracks_per_album()
        tracks = [
            track
            for album in albums
            for track in self.music_util.get_most_popular_tracks(
                album, num_tracks_per_album)
        ]

        playlist_title = get_new_playlist_name()
        self.info_logger(f"Creating '{playlist_title}' playlist...")
        self.my_music_lib.create_playlist(
            playlist_title,
            [track.uri for track in tracks],
            description="created by playlist_creator"
        )

        self.info_logger(f"Playlist created!")
        return albums

    def duplicate_and_reduce_num_tracks_per_album(self, get_playlist, get_new_playlist_name, get_num_tracks_per_album):
        tracks_by_album = defaultdict(list)
        playlist = get_playlist()
        for track in playlist.tracks:
            tracks_by_album[track.album_id].append(track)

        most_popular_tracks_per_album = []
        # TODO: use music_util.get_tracks_most_popular_first(album) ?
        num_tracks_per_album = get_num_tracks_per_album()
        for _, tracks in tracks_by_album.items():
            tracks_sorted_by_popularity = sorted(
                tracks, key=lambda track: track.popularity, reverse=True)
            most_popular_tracks_per_album.extend(
                tracks_sorted_by_popularity[:num_tracks_per_album])

        new_playlist_name = get_new_playlist_name()
        self.info_logger(f"Created your new playlist '{new_playlist_name}' containing {len(most_popular_tracks_per_album)} tracks!")

        track_uris = [track.id for track in most_popular_tracks_per_album]
        shuffle(track_uris)
        self.my_music_lib.create_playlist(new_playlist_name, track_uris)