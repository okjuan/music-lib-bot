![Spotify Playlist](https://github.com/okjuan/music-lib-bot/raw/master/imgs/sample3.png)

### What is this?
An interactive app for creating and updating your Spotify playlists. It does stuff like this:
- Look at your recently saved albums
- Group albums by genres
- Let you select a playlist to create from a list of options
- Create a chronological playlist from an artist's discrography
- Create a shuffled playlist based on an existing playlist full of albums

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
$ python app/music_lib_bot.py

> What app do you want to use? Pick an option:
	'a' - Playlist Updater
	'b' - Playlist Creator
	'q' - quit
b

> Minimum # of genres per playlist? default is 4
2

> Should I look at your entire library? y or n - default is n
n

> # of albums to fetch from your library? default is 50
9
Fetching recently saved albums...
Fetched 9 albums...
Grouping 9 albums...
Matched into 6 groups...

> Minimum # of albums per playlist? default is 4
2

> Minimum # of artists per playlist? default is 4
2

Here are your options for creating a playlist from albums in your library.
The options are ordered by number of albums from most to least.
#0
	Description: conscious hip hop, hip hop, rap
	Number of albums: 4
	Artists: Joey Bada$$, Gang Starr
#1
	Description: alternative hip hop, hip hop
	Number of albums: 4
	Artists: BADBADNOTGOOD, The Pharcyde, Gang Starr
#2
	Description: hip hop, rap
	Number of albums: 3
	Artists: Joey Bada$$, The Pharcyde
#3
	Description: alternative hip hop, hardcore hip hop, hip hop, rap
	Number of albums: 3
	Artists: The Pharcyde, Gang Starr

> Please select which playlist to create!
Enter a number between 0 and 3 or enter -1 to quit:
3

> How many tracks per album per playlist? default is 3

Creating 'alternative hip hop, hardcore hip hop, hip hop, rap' playlist from 3 albums...
Playlist created!

> Create another playlist? y or n - default is 'y'
n
Thanks for using Playlist Picker, see ya later!

> What app do you want to use? Pick an option:
	'a' - Playlist Updater
	'b' - Playlist Creator
	'q' - quit
a

> What's the name of your playlist?
alternative hip hop, hardcore hip hop, hip hop, rap

> # of tracks per album to add to playlist? default is 3


> # of albums to fetch from your library? default is 50
20
Your playlist's most common genres are: hardcore hip hop
Fetching recently saved albums...
Fetched 20 albums...
Grouping 20 albums...
Matched into 23 groups...
Good news! I found 12 album(s) matching your playlist's genres:
- Moment Of Truth by Gang Starr
- Midnight Marauders by A Tribe Called Quest
- Enter The Wu-Tang (36 Chambers) [Expanded Edition] by Wu-Tang Clan
- Adrian Younge Presents: 12 Reasons To Die II by Ghostface Killah, Adrian Younge, Linear Labs
- Hard To Earn by Gang Starr
- Only Built 4 Cuban Linx... by Raekwon
- Liquid Swords by GZA
- Enta Da Stage by Black Moon
- A Future Without A Past by Leaders of the New School
- Labcabincalifornia (Deluxe Edition) by The Pharcyde
- Da Storm by O.G.C.
- The Low End Theory by A Tribe Called Quest
Found 12 albums in your library that contain genres: hardcore hip hop
Oh! Skipping album 'Moment Of Truth' because it's already in the playlist.
Oh! Skipping album 'Hard To Earn' because it's already in the playlist.
Oh! Skipping album 'Labcabincalifornia (Deluxe Edition)' because it's already in the playlist.
Found 27 tracks with similar genres to those already in your playlist..
Adding 27 randomly throughout your playlist: 'alternative hip hop, hardcore hip hop, hip hop, rap'

> Make more changes? y or no - default is 'n'
n
Thanks for using Playlist Updater, catch ya next time.

> What app do you want to use? Pick an option:
	'a' - Playlist Updater
	'b' - Playlist Creator
	'q' - quit
q
Happy listening!
```

### Testing
```
$ python run_tests.py

$ python run_tests.py TestSpotifyClientWrapper

$ python run_tests.py TestPlaylistPicker

$ python run_tests.py TestMyMusicLib

$ python run_tests.py TestMusicUtil
```
