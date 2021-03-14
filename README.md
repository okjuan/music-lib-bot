### What is this?
A program that looks at your recently saved albums on Spotify and adds songs from them into your Spotify playlists. (Well, that's what it's going to be.)

### Pre-requisites
- Python 3.6 or greater
- [spotipy](https://pypi.org/project/spotipy/) installed
- Spotify Developer account
- Spotify Application with a redirect URI e.g. `https://localhost:5000`
- environment variables `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URI` set with the values from your registered Spotify Application

### Running the Program
#### The First Time
When you run `python music_lib_bot.py` for the first time, a browser window should open. It will prompt you to give permissions to read your Spotify music library and modify your private playlists. Once you give permissions, it will redirect you to whatever redirect URI you configured for your Spotify app on the Spotify Developer dashboard e.g.`https://localhost:5000`. Copy that URL. The program on the command line should prompt you for it. Paste the URL you copied into the command line.

#### Every Other Time
Just run it!
```
python music_lib_bot.py
```