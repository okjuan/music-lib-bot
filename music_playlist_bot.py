from music_lib_api import (
    create_playlist,
    get_tracks_from_each,
    get_my_albums_grouped_by_genre
)


SELECTION_MAPPING = []
SELECTION_LOWER_BOUND, SELECTION_UPPER_BOUND = -1, -1

def print_all_genre_groups(albums_by_genre):
    global SELECTION_LOWER_BOUND, SELECTION_UPPER_BOUND
    SELECTION_LOWER_BOUND, count = 0, 0
    print("Here are your options:")
    for genre_group, albums in albums_by_genre.items():
        print(f"\n#{count} --- {len(albums)} albums based on these genres:\n{genre_group}")
        SELECTION_MAPPING.append(genre_group)
        count += 1
    SELECTION_UPPER_BOUND = count

def get_user_selection():
    if SELECTION_LOWER_BOUND >= SELECTION_UPPER_BOUND:
        print("Looks like there was nothing to select from!")
        return None

    selection = None
    while selection is None:
        selection = parse_selection(
            input(
                f"Please select which playlist to create!\nEnter a number between 0 and {len(SELECTION_MAPPING)}:\n"
            )
        )
    return SELECTION_MAPPING[selection]

def parse_selection(selection):
    try:
        selection_int = int(selection.strip())
    except ValueError:
        return None

    if selection_int >= SELECTION_LOWER_BOUND and selection_int <= SELECTION_UPPER_BOUND:
        return selection_int
    else:
        return None

def get_selected_albums(albums_by_genre):
    print_all_genre_groups(albums_by_genre)

    selected_genre_group = get_user_selection()
    if selected_genre_group is None:
        print("Looks like there was nothing to select from!")
        return None

    return (selected_genre_group, albums_by_genre[selected_genre_group])

def create_playlist_from_albums(albums, description):
    print(f"Creating '{description}' playlist from {len(albums)} albums...")
    create_playlist(
        "created by music.lib.bot",
        get_tracks_from_each(albums),
        description=description
    )

def playlist_picker():
    albums_by_genre = get_my_albums_grouped_by_genre()
    description, albums = get_selected_albums(albums_by_genre)
    if albums is not None and len(albums) > 0:
        create_playlist_from_albums(albums, description)
    print(f"All done. Happy listening!")


if __name__ == "__main__":
    playlist_picker()