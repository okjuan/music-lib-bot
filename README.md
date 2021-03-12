### Pre-requisites
- Python 3.6 or greater
- [spotipy](https://pypi.org/project/spotipy/) installed
- Spotify Developer account
- Spotify Application with a redirect URI e.g. `https://localhost:5000`
- environment variables `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URI` set with the values from your registered Spotify Application

### Running the Program
When you run `python music.lib.bot.py`, a browser window should open. It will prompt you to give permissions to read your Spotify music library. Once you give permissions, it will redirect you to whatever redirect URI you configured for your Spotify app on the Spotify Developer dashboard e.g.`https://localhost:5000`. Copy that URL. The program on the command line should prompt you for a redirect URL. Paste the URL you copied into the command line.