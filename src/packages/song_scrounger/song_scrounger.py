import re

from collections import defaultdict
from functools import reduce

from .util import read_file_contents


class SongScrounger:
    def __init__(self, spotify_client):
        self.spotify_client = spotify_client

    async def find_songs(self, input_file_path):
        text = read_file_contents(input_file_path)
        songs = await self.find_media_items(text, self.spotify_client.find_song)
        return songs

    async def find_albums(self, input_file_path):
        text = read_file_contents(input_file_path)
        albums = await self.find_media_items(text, self.spotify_client.find_album)
        return albums

    async def find_media_items(self, text, name_lookup):
        """Parses given text for names of media items (songs or albums),
        matching with artists if mentioned.

        Each name is searched using the given name_lookup function.
        The artists in the search results are searched for in the text as well.
        Any matches are used for media item disambiguation.

        Params:
            text (str): containing 1 or more paragraphs containing
                song or album names, and, optionally, their artists.
            name_lookup (asyn func): given a name (str), returns an object (e.g. Song, Album).

        Returns:
            (dict): key (str) is name; val (set(Song|Album)) of matching media items.
        """
        results = defaultdict(set)
        paragraphs = self._get_paragraphs(text)
        for paragraph in paragraphs:
            names = self.find_names(paragraph)
            for name in names:
                media_items = await name_lookup(name)
                media_items = self.filter_if_any_artists_mentioned_greedy(media_items, paragraph, text)
                media_items = self.reduce_by_popularity_per_artist(media_items)
                results[name] = self.set_union(results[name], media_items)
        return results

    def filter_if_any_artists_mentioned_greedy(self, songs_or_albums, subset_text, whole_text):
        filtered = self.filter_if_any_artists_mentioned(songs_or_albums, subset_text)
        if len(filtered) > 1 and len(filtered) == len(songs_or_albums):
            filtered = self.filter_if_any_artists_mentioned(songs_or_albums, whole_text)
        return filtered

    def set_union(self, song_or_album_set_A, song_or_album_set_B):
        spotify_uris_seen_already, union = set(), set()
        for song_or_album in song_or_album_set_A | song_or_album_set_B:
            if song_or_album.spotify_uri not in spotify_uris_seen_already:
                union.add(song_or_album)
                spotify_uris_seen_already.add(song_or_album.spotify_uri)
        return union

    def filter_if_any_artists_mentioned(self, songs_or_albums, text):
        """
        Params:
            songs_or_albums (set(Song)).
            text (str).

        Return:
            (set(Song)).
        """
        with_mentioned_artists = self.filter_by_mentioned_artist(songs_or_albums, text)
        if len(with_mentioned_artists) == 0:
            return set(songs_or_albums)
        return with_mentioned_artists

    def filter_by_mentioned_artist(self, songs_or_albums, text):
        """Returns only songs_or_albums whose artist(s) is/are mentioned in the text.
        Params:
            songs_or_albums (set(Song|Album)).
            text (str).

        Return:
            (set(Song|Album)).
        """
        with_mentioned_artists = set()
        for song_or_album in songs_or_albums:
            for artist in song_or_album.artists:
                if self.is_mentioned(artist, text):
                    with_mentioned_artists.add(song_or_album)
        return with_mentioned_artists

    def is_mentioned(self, artist, text):
        return (
            self.is_mentioned_verbatim(artist, text) or
            self.is_mentioned_in_parts(artist, text) or
            self.is_partially_mentioned(artist, text)
        )

    def reduce_by_popularity_per_artist(self, songs_or_albums):
        return set([
            self.pick_most_popular(dups)
            for dups in self.group_by_artist(songs_or_albums)
        ])

    def group_by_artist(self, songs_or_albums):
        cache_key_from_artists = lambda artists: "-".join(artists)
        by_same_artist = defaultdict(set)
        for song_or_album in songs_or_albums:
            by_same_artist[cache_key_from_artists(song_or_album.artists)].add(song_or_album)
        return by_same_artist.values()

    def pick_most_popular(self, songs_or_albums):
        def pick_more_popular(song_or_album1, song_or_album2):
            if song_or_album1.popularity is None:
                raise ValueError(f"{song_or_album1.name}'s popularity is None")
            elif song_or_album2.popularity is None:
                raise ValueError(f"{song_or_album2.name}'s popularity is None")
            return song_or_album1 if song_or_album1.popularity >= song_or_album2.popularity else song_or_album2
        return reduce(pick_more_popular, songs_or_albums)

    def is_mentioned_verbatim(self, word, text):
        """True iff text contains word, ignoring case.

        Params:
            word (str): e.g. "Hello".
            text (str): e.g. "Hello dear".
        """
        word, text = word.lower(), text.lower()
        return self.is_mentioned_as_full_str(word, text)

    def is_partially_mentioned(self, word, text):
        """

        e.g. "Lonnie Donnegan & His Skiffle Group" is deemed mentioned
        in the text "The artist Lonnie Donnegan".

        Params:
            word (str): e.g. "Lonnie Donnegan & His Skiffle Group".
            text (str): e.g. "The artist Lonnie Donnegan".
        """
        word = word.lower()
        separators = ["and", "&", "band"]
        for separator in separators:
            trimmed_word = word.split(separator)[0].strip()
            if self.is_mentioned_verbatim(trimmed_word, text):
                return True
        return False

    def is_mentioned_in_parts(self, word, text):
        word, text = word.lower(), text.lower()
        word_tokens = word.split(" ")
        for token in word_tokens:
            if not self.is_mentioned_as_full_str(token, text):
                return False
        return True

    def is_mentioned_as_full_str(self, word, text):
        return len(self.find_occurrences(word, text)) > 0 or self.is_mentioned_as_synonym(word, text)

    def is_mentioned_as_synonym(self, word, text):
        synonyms = [{"and", "&"}]
        for synonym_set in synonyms:
            if word in synonym_set:
                for synonym in synonym_set:
                    if len(self.find_occurrences(synonym, text)) > 0:
                        return True
        return False

    def find_occurrences(self, word, text):
        """Returns list of occurrences iff 'word' occurs in 'text' but not as a substring of another word.

        Case-sensitive. Can be made case-insensitive by lowering args before calling.

        Params:
            word (str): e.g. "Hello".
            text (str): e.g. "Hello, how are you?".

        Returns:
            ([string]): e.g. ["Hello"]
        """
        return re.findall(f"(^|[^a-zA-Z]){word}([^a-zA-Z]|$)", text)

    def _get_paragraphs(self, text):
        "Returns non-empty paragraphs with one or more non-whitespace characters."
        paragraphs = text.split("\n")
        return [p for p in paragraphs if len(p.strip(" ")) > 0]

    def find_names(self, text):
        """Retrieves quoted strings in text

        Removes whitespace at start and end, and punctuation at the end.

        Params:
            text (str): e.g. "I keep using the example \"Sorry\" by Justin Bieber"
        """
        tokens = self.find_quoted_tokens(text)
        tokens = map(lambda token: token.strip(" "), tokens)
        return map(lambda token: token.rstrip(",."), tokens)

    def find_quoted_tokens(self, text):
        """Retrieves all quoted strings in the order they occur in the given text.
        Params:
            text (str).

        Returns:
            tokens (list): strings found between quotes.

        Notes:
            - Ignores trailing quote if quotes are unbalanced
            - Skips empty tokens
        """
        tokens = re.findall("\"([^\"]*)\"", text)
        return [token for token in tokens if len(token.strip(" ")) > 0]