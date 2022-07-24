# allows me to run:
# $ python scripts/this_script.py
import sys
sys.path.extend(['.', '../'])

from app.lib.console_ui import ConsoleUI
from app.music_lib_bot import MusicLibBot
from packages.music_management.music_util import MusicUtil
from packages.music_management.my_music_lib import MyMusicLib
from packages.music_api_clients.spotify import Spotify


def main():
    spotify = Spotify()
    ui = ConsoleUI()
    music_util = MusicUtil(spotify, ui.tell_user)
    my_music_lib = MyMusicLib(spotify, music_util, ui.tell_user)
    music_lib_bot = MusicLibBot(spotify, my_music_lib, music_util, ui)

    music_lib_bot.run_interactive_playlist_picker()
    music_lib_bot.run_create_playlist_from_an_artists_discography()
    music_lib_bot.run_create_playlist_based_on_existing_playlist()
    music_lib_bot.run_create_or_update_target_from_seed()
    music_lib_bot.run_interactive_playlist_picker()
    music_lib_bot.run_add_tracks_from_my_saved_albums_with_similar_genres()
    music_lib_bot.run_add_recommended_tracks_with_similar_attributes()

    music_lib_bot.run()


if __name__ == "__main__":
    main()