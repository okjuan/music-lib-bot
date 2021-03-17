from music_lib_api import (
    create_playlist,
    get_tracks_from_each,
    get_my_albums_grouped_by_genre
)


SELECTION_QUIT_APP = "Quit"
QUIT_KEY = "q"
MIN_GROUP_SIZE = 1

def set_up_options(albums_by_genre):
    return [
        dict(description=genre_group, albums=albums)
        for genre_group, albums in albums_by_genre.items()
        if len(albums) >= MIN_GROUP_SIZE
    ]

def print_playlist_options(options):
    print("\nHere are your options for creating a playlist from albums in your library:")
    for idx, album_groups in enumerate(options):
        print(f"#{idx}\n\tDescription: {album_groups['description']}\n\tNumber of albums: {len(album_groups['albums'])}")
    print()

def get_user_selection(min_option, max_option):
    selection = None
    while selection is None:
        selection = parse_selection(min_option, max_option)
    return selection

def parse_selection(min_option, max_option):
    selection = input(
        f"Please select which playlist to create!\nEnter a number between {min_option} and {max_option} or enter '{QUIT_KEY}' to quit:\n")

    if selection.strip() == QUIT_KEY:
        return SELECTION_QUIT_APP

    try:
        selection_int = int(selection.strip())
    except ValueError:
        return None

    if selection_int >= min_option and selection_int <= max_option:
        return selection_int
    return None

def get_selection(options):
    print_playlist_options(options)
    selection = get_user_selection(0, len(options)-1)
    return selection

def create_playlist_from_albums(album_group):
    print(f"Creating '{album_group['description']}' playlist from {len(album_group['albums'])} albums...")
    create_playlist(
        "created by music.lib.bot",
        get_tracks_from_each(album_group["albums"]),
        description=album_group["description"]
    )

def launch_playlist_picker_ui(options):
    while True:
        selection = get_selection(options)
        if selection is SELECTION_QUIT_APP:
            print("Quitting...")
            break
        create_playlist_from_albums(options[selection])

def playlist_picker():
    albums_by_genre = get_my_albums_grouped_by_genre()

    options = set_up_options(albums_by_genre)
    if len(options) == 0:
        print("Didn't find any options to select from!")
        return

    launch_playlist_picker_ui(options)

    print(f"Happy listening!")


if __name__ == "__main__":
    playlist_picker()