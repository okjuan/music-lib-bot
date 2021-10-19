class MusicLibBotHelper:
    def __init__(self, my_music_lib, ui):
        self.my_music_lib = my_music_lib
        self.ui = ui

    def get_playlist_name_from_user(self):
        playlist = None
        while playlist is None:
            playlist_name = self.ui.get_string("What's the name of your playlist?")
            playlist = self.my_music_lib.get_playlist_by_name(playlist_name)
            if playlist is None:
                self.ui.tell_user(f"I couldn't find '{playlist_name}' in your playlists.")
        return playlist