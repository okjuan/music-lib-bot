![Spotify Playlist](https://github.com/okjuan/music-lib-bot/raw/master/imgs/sample2.png)

```
$ python playlist_picker.py
Fetching recently saved albums...
Fetched 10 albums...
Grouping 10 albums...
Matched into 7 groups...

Here are your options:

#0 --- 3 albums based on these genres:
alternative rock, art rock, dance rock, experimental, new wave, post-punk, punk, uk post-punk

#1 --- 2 albums based on these genres:
art punk, art rock, dance rock, dance-punk, experimental, new wave, post-punk, punk, uk post-punk

#2 --- 2 albums based on these genres:
alternative rock, art punk, art rock, dance rock, dance-punk, experimental, new wave, post-punk, punk, uk post-punk

#3 --- 4 albums based on these genres:
alternative rock, art rock, dance rock, new wave, post-punk, uk post-punk

#4 --- 2 albums based on these genres:
art rock, dance rock, experimental, new romantic, new wave, post-punk, punk, uk post-punk

#5 --- 2 albums based on these genres:
art punk, art rock, dance rock, dance-punk, experimental, new wave, post-punk, pub rock, punk, uk post-punk

#6 --- 2 albums based on these genres:
art rock, dance rock, madchester, new wave, post-punk, uk post-punk

Please select which playlist to create!
Enter a number between 0 and 7:
3

Creating 'alternative rock, art rock, dance rock, new wave, post-punk, uk post-punk' playlist from 4 albums...
All done. Happy listening!
```

### What is this?
An interactive app that looks at your recently saved albums on Spotify, groups them by their genres, and lets you select which groups to make into Spotify playlists.

### Pre-requisites
- Python 3.6 or greater
- [spotipy](https://pypi.org/project/spotipy/) installed
- Spotify Developer account
- Spotify Application with a redirect URI e.g. `https://localhost:5000`
- environment variables `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URI` set with the values from your registered Spotify Application

### Running the Program
#### The First Time
When you run `python playlist_picker.py` for the first time, a browser window should open. It will prompt you to give permissions to read your Spotify music library and modify your private playlists. Once you give permissions, it will redirect you to whatever redirect URI you configured for your Spotify app on the Spotify Developer dashboard e.g.`https://localhost:5000`. Copy that URL. The program on the command line should prompt you for it. Paste the URL you copied into the command line.

#### Every Other Time
Just run it!
```
python playlist_picker.py
```
