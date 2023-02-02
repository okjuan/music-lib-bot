![Spotify Playlist](https://github.com/okjuan/music-lib-bot/raw/master/imgs/sample3.png)

### What is this?
An interactive app for creating and updating your Spotify playlists. It does stuff like this:
- Create a chronological playlist from an artist's discrography
- Create a shuffled playlist based on an existing playlist full of albums
- Update a playlist with recommended songs based on the playlist's songs and their attributes
- Look at your saved albums
- Group albums by genres
- Offer to create suggested playlists based on grouped albums
- Pick most popular songs from each album

### Pre-requisites
- Python 3.6 or greater
- [spotipy](https://pypi.org/project/spotipy/) installed
- Spotify Developer account
- Spotify Application with a redirect URI e.g. `https://localhost:5000`
- environment variables `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URI` set with the values from your registered Spotify Application

### Running the Program for the First Time
When you run `python music_lib_bot.py` for the first time, a browser window should open. It will prompt you to give permissions to read your Spotify music library and modify your private playlists. Once you give permissions, it will redirect you to whatever redirect URI you configured for your Spotify app on the Spotify Developer dashboard e.g.`https://localhost:5000`. Copy that URL. The program on the command line should prompt you for it. Paste the URL you copied into the command line.

### Example: Create a Playlist from an Artist's Discography
```
$ python app/music_lib_bot.py

Here are your options:
(0): Create playlist from an artist's discography.
(1): Create playlist from a playlist full of albums.
(2): Create playlist from albums in your library that have matching genres.
(3): Update existing playlist with tracks from my saved albums with similar genres.
(4): Update existing playlist with recommended tracks with similar attributes.

> Pick an option!
Enter a number between 0 and 4 or enter -1 to quit:
0

> What artist interests you?
Jay-Z
I found: JAY-Z, with genres ['east coast hip hop', 'hip hop', 'rap'], with popularity 85
Out of the total 52 number of albums...
Only 22 are essential; the rest are duplicates, demos, and live albums.

> How many tracks do you want from each album?
1

> What do you want to call your playlist?
Hova!
Creating 'Hova!' playlist...
Playlist created!
```

![Discography Playlist](https://github.com/okjuan/music-lib-bot/raw/master/imgs/discographyPlaylist.Example.png)

### Example: Add Songs to Your Existing Playlist from Your Saved Albums
```
$ python app/music_lib_bot.py

Here are your options:
(0): Create playlist from an artist's discography.
(1): Create playlist from a playlist full of albums.
(2): Create playlist from albums in your library that have matching genres.
(3): Update existing playlist with tracks from my saved albums with similar genres.
(4): Update existing playlist with recommended tracks with similar attributes.

> Pick an option!
Enter a number between 0 and 4 or enter -1 to quit:
3

> What's the name of your playlist?
Hova!
The genres that all tracks in your playlist have in common are hip hop, rap, east coast hip hop

> # of albums to fetch from your library? default is 50

Grouping 60 albums...
Matched into 48 groups...
Good news! I found 5 album(s) matching your playlist's genres:
- Illmatic by Nas
- The Infamous by Mobb Deep
- Enter The Wu-Tang (36 Chambers) [Expanded Edition] by Wu-Tang Clan
- MM...FOOD by MF DOOM
- Operation: Doomsday (Complete) by MF DOOM
Found 5 albums in your library that exactly match genres: hip hop, rap, east coast hip hop

> # of tracks per album to add to playlist? default is 3

Found 15 tracks with exact same genres as those already in your playlist..
Adding 15 randomly throughout your playlist: 'Hova!'
```

![Updated Playlist](https://github.com/okjuan/music-lib-bot/raw/master/imgs/updatePlaylist.fromSavedAlbumsWithSameGenres.example.png)


### Testing
```
python run_tests.py
python run_tests.py TestSpotify
python run_tests.py TestMusicLibBot
python run_tests.py TestMyMusicLib
python run_tests.py TestMusicUtil
python run_tests.py TestPlaylistAnalyzer
```
