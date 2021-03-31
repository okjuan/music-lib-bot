from collections import defaultdict


class MusicUtil:
    def __init__(self, spotify_client_wrapper):
        self.spotify_client_wrapper = spotify_client_wrapper

    def get_artist_genres(self, album):
        return [
            genre
            for artist in album['artists']
            for genre in self.spotify_client_wrapper.get_artist_genres(artist['id'])
        ]

    def _add_artist_genres(self, albums):
        albums_by_id = dict()
        for album in albums:
            album['genres'] = self.get_artist_genres(album)
            albums_by_id[album['id']] = album
        return albums_by_id

    def _detect_genre_matches(self, albums_by_id):
        adjacencies, genre_to_albums = defaultdict(lambda: defaultdict(list)), defaultdict(set)
        for _, album in albums_by_id.items():
            for genre in album['genres']:
                for matching_album_id in genre_to_albums[genre]:
                    adjacencies[album['id']][matching_album_id].append(genre)
                    adjacencies[matching_album_id][album['id']].append(genre)
                genre_to_albums[genre].add(album['id'])
        return adjacencies

    def _as_readable_key(self, list_):
        list_.sort()
        return ", ".join(list_) if len(list_) > 0 else "unknown"

    def _group_albums(self, album_ids, matches):
        if len(album_ids) == 0 or len(matches) == 0:
            return [album_ids]

        grouped_albums = dict()
        for album_id in album_ids:
            for matching_album_id, matched_on in matches[album_id].items():
                group_key = self._as_readable_key(matched_on)
                if group_key not in grouped_albums:
                    grouped_albums[group_key] = {"num matches": 0, "album ids": set()}
                grouped_albums[group_key]["num matches"] = len(matched_on)
                grouped_albums[group_key]["album ids"].add(album_id)
                grouped_albums[group_key]["album ids"].add(matching_album_id)
        return grouped_albums

    def group_albums_by_genre(self, albums, min_genres_per_group):
        """
        Returns:
            albums_by_genre (dict): key:string, value:[Album].
                e.g. {'rock': [Album], 'jazz': [Album, Album]}.
        """
        albums_by_id = self._add_artist_genres(albums)
        matches = self._detect_genre_matches(albums_by_id)
        album_groups = self._group_albums(albums_by_id.keys(), matches)
        return {
            description: [albums_by_id[album_id] for album_id in group["album ids"]]
            for description, group in album_groups.items()
            if group["num matches"] >= min_genres_per_group
        }