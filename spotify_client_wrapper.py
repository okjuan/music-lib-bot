from spotipy.oauth2 import SpotifyOAuth
import spotipy

SPOTIFY_ALBUMS_API_LIMIT = 50
SPOTIFY_SCOPES = "user-library-read,playlist-modify-private,playlist-modify-private,playlist-read-private,playlist-read-collaborative"


class SpotifyClientWrapper:
    def __init__(self):
        auth = SpotifyOAuth(scope=SPOTIFY_SCOPES)
        self.client = spotipy.Spotify(auth_manager=auth)

    def get_current_user_playlist(self, name):
        num_playlists_fetched = 0
        while True:
            playlists = self.client.current_user_playlists(
                offset=num_playlists_fetched).get('items', [])
            if len(playlists) == 0:
                break
            num_playlists_fetched += len(playlists)
            for p in playlists:
                if p['name'] == name:
                    return p
        return None

    def get_artist_genres(self, artist_id):
        return self.client.artist(artist_id)['genres']

    def get_my_albums(self, max_albums_to_fetch):
        print(f"Fetching recently saved albums...")
        albums, albums_fetched_so_far = [], 0
        while albums_fetched_so_far < max_albums_to_fetch:
            max_batch_size = max_albums_to_fetch - albums_fetched_so_far

            batch_size = max_batch_size if max_batch_size <= SPOTIFY_ALBUMS_API_LIMIT else SPOTIFY_ALBUMS_API_LIMIT
            results = self.client.current_user_saved_albums(
                limit=batch_size, offset=albums_fetched_so_far)

            if len(results['items']) == 0:
                print(f"No albums left to fetch...")
                break

            albums.extend([album['album'] for album in results['items']])
            albums_fetched_so_far += batch_size

        print(f"Fetched {len(albums)} albums...")
        return albums