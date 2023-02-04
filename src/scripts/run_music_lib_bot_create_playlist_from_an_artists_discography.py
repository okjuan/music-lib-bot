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

    music_lib_bot.run_create_playlist_from_an_artists_discography()


if __name__ == "__main__":
    main()