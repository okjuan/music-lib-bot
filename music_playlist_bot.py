from music_lib_api import (
    create_playlist,
    get_tracks_from_each,
    get_my_albums_grouped_by_genre
)


SELECTION_MAPPING = []
SELECTION_LOWER_BOUND, SELECTION_UPPER_BOUND = -1, -1
SELECTION_QUIT_APP = "Quit"
MIN_GROUP_SIZE = 5

def set_up_selections(albums_by_genre):
    global SELECTION_LOWER_BOUND, SELECTION_UPPER_BOUND
    SELECTION_LOWER_BOUND, count = 0, 0
    for genre_group, albums in albums_by_genre.items():
        if len(albums) >= MIN_GROUP_SIZE:
            SELECTION_MAPPING.append(genre_group)
            count += 1
    SELECTION_UPPER_BOUND = count

def print_all_genre_groups():
    print("Here are your options for creating a playlist from albums in your library:")
    for idx, option in enumerate(SELECTION_MAPPING):
        print(f"\n#{idx} --- playlist from these genres:\n{option}")

def get_user_selection():
    if SELECTION_LOWER_BOUND >= SELECTION_UPPER_BOUND:
        print("Looks like there was nothing to select from!")
        return None

    selection = None
    while selection is None:
        selection = parse_selection(
            input(
                f"Please select which playlist to create!\nEnter a number between 0 and {len(SELECTION_MAPPING)} or enter 'q' to quit:\n"
            )
        )
    return selection

def parse_selection(selection):
    if selection.strip() == "q":
        return SELECTION_QUIT_APP

    try:
        selection_int = int(selection.strip())
    except ValueError:
        return None

    if selection_int >= SELECTION_LOWER_BOUND and selection_int <= SELECTION_UPPER_BOUND:
        return selection_int
    else:
        return None

def get_selection(albums_by_genre):
    print_all_genre_groups()
    selection = get_user_selection()
    return selection

def create_playlist_from_albums(albums, description):
    print(f"Creating '{description}' playlist from {len(albums)} albums...")
    create_playlist(
        "created by music.lib.bot",
        get_tracks_from_each(albums),
        description=description
    )

def playlist_picker():
    albums_by_genre = get_my_albums_grouped_by_genre()
    set_up_selections(albums_by_genre)
    while True:
        selection = get_selection(albums_by_genre)
        if selection is SELECTION_QUIT_APP:
            print("Quitting...")
            break
        genre_group = SELECTION_MAPPING[selection]
        create_playlist_from_albums(albums_by_genre[genre_group], genre_group)
    print(f"Happy listening!")


if __name__ == "__main__":
    playlist_picker()