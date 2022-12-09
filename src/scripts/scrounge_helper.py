def print_summary_of_song_matches(songs):
    song_names = list(songs.keys())
    number_of_songs_found = len(song_names)
    if number_of_songs_found == 0:
        print(f"Didn't find any songs!")
        return

    song_name1 = song_names[0]
    song_name2 = song_names[1] if number_of_songs_found > 1 else None
    song_name_examples = song_name1 + (f" and {song_name2}" if song_name2 is not None else "")
    print(f"\nFound {number_of_songs_found} songs, including {song_name_examples}.")

    for song_name, songs in songs.items():
        print(f"- Found {len(songs)} matches for song '{song_name}'")
        for match in songs:
            artists = ", ".join([artist.name for artist in match.artists])
            print(f"  - '{match.name}' by {artists}, with Spotify URI {match.spotify_uri}")
