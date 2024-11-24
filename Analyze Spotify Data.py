import json
from datetime import datetime, timedelta, timezone
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import timeit
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from dotenv import load_dotenv
import argparse
matplotlib.use('Qt5Agg')

data = list()

with open('AllData.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

with open('PastYearData.json', 'r', encoding='utf-8') as file:
    data.extend(json.load(file))

with open('Airflow/data/SelfCollectedData.json', 'r', encoding='utf-8') as file:
    data.extend(json.load(file))

ms: int

load_dotenv()
scope = 'playlist-read-private'
auth_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager, retries=0)

def main():
    global songs
    global artists
    global prevSongs
    global prevArtists

    # Parse args
    parser = argparse.ArgumentParser()
    addStatsArgs(parser)
    args = parser.parse_args()

    init(args)

    while True:
        type_args = getTypeArgs()

        # Manage changing default ranges
        tempCalc = False
        if type_args.type == 'r':
            init(type_args)

        elif (type_args.eo != None or type_args.ed != None) or (type_args.ld != None or type_args.lw != None or type_args.lm != 1):
            tempCalc = True

        # Temporarily set stats to new values
        if tempCalc:
            storedStats = {
                'songs': songs,
                'artists': artists,
                'prevSongs': prevSongs,
                'prevArtists': prevArtists
            }
            init(type_args)
        
        if type_args.type == 't':
            if type_args.n != False:
                top(songs, prevSongs, type_args.n)
            else:
                top(songs, prevSongs)
        elif type_args.type == 'a':
            top(artists, prevArtists)
        elif type_args.type == 'sh':
            topHistory(input('Artist: ') + ": " + input('Song: '), True, timedelta(weeks=type_args.w), basedOnRank=not type_args.n)
        elif type_args.type == 'ah':
            topHistory(input('Artist: '), False, timedelta(weeks=type_args.w), basedOnRank=not type_args.n)
        elif type_args.type == 'n':
            topNewSongs()
        elif type_args.type == 'f':
            findSong(input('Song: '))
        elif type_args.type == 'fa':
            findArtist(input('Artist: '))
        elif type_args.type == 'g':
            analyzeSongStats()

        # Reset stats back
        if tempCalc:
            setStats(storedStats)

def init(args: argparse.Namespace) -> None:
    global ms; ms = 0

    if args.eo != None:
        endTime = getStartOfWeek(datetime.now(tz=timezone.utc) - timedelta(weeks=args.eo))
    elif args.ed != None:
        endTime = getStartOfWeek(datetime.fromisoformat(args.ed))
    else:
        endTime = datetime.now(tz=timezone.utc)

    if args.ld != None:
        timeLength = timedelta(days=args.ld)
    elif args.lw != None:
        timeLength = timedelta(weeks=args.lw)
    else:
        timeLength = timedelta(days=30.43685*args.lm)
    
    currStats = getStats(endTime, timeLength)
    print(f"Minutes: {(ms/60000):.2f}")
    prevStats = getStats(getStartOfWeek(endTime-timedelta(hours=2)), timeLength)
    stats = {
        "songs" : currStats[0],
        "artists" : currStats[1],
        "prevSongs" : prevStats[0],
        "prevArtists": prevStats[1],
    }
    setStats(stats)

def setStats(stats: dict) -> None:
    global songs
    global artists
    global prevSongs
    global prevArtists

    songs = stats['songs']
    artists = stats['artists']
    prevSongs = stats['prevSongs']
    prevArtists = stats['prevArtists']

def getTypeArgs() -> argparse.Namespace:
    type_parser = argparse.ArgumentParser()
    type_parser.add_argument("type", type=str, help="the type of anaylsis to perform")
    type_parser.add_argument("-n", nargs="?", type=int, const=True, default=False, help="display number of streams")
    type_parser.add_argument("-w", default=24, type=int, help="total number of weeks to calculate")
    
    addStatsArgs(type_parser)

    type_args = type_parser.parse_args(input("Type of Analysis: ").split())
    return type_args

def addStatsArgs(parser: argparse.ArgumentParser):
    endDateGroup = parser.add_mutually_exclusive_group()
    endDateGroup.add_argument("-eo", type=int, help="end date offset")
    endDateGroup.add_argument("-ed", type=str, help="end date")
    lengthGroup = parser.add_mutually_exclusive_group()
    lengthGroup.add_argument("-ld", type=int, help="total number of days to calculate")
    lengthGroup.add_argument("-lw", type=int, help="total number of weeks to calculate")
    lengthGroup.add_argument("-lm", default=1, type=int, help="total number of months to calculate")
    return parser
    
def getStats(endTime: datetime, length: timedelta, songStats=True, artistStats=True) -> list:
    endTime = endTime.replace(tzinfo=None)
    songs = []
    artists = []
    global ms
    for play in data[::-1]:
        if not (endTime-length <= datetime.fromisoformat(play['endTime']) <= endTime):
            continue
        # if not (datetime.fromisoformat("2024-01-01") <= datetime.fromisoformat(play['endTime']) <= datetime.fromisoformat("2024-11-30")):
        #     continue
        
        ms += play['msPlayed']

        if play['msPlayed'] < 30000:
            continue
        if play['artists'][0] == "Unknown Artist" and play['trackName'] == "Unknown Track":
            continue
        
        # Track Songs
        if songStats:
            trackName = (play['artists'][0] if type(play['artists']) == list else play['artists']) + ": " + play['trackName']
            try:
                index = [d['name'].lower() for d in songs].index(trackName.lower())
                songs[index]['timesPlayed'] += 1
            except ValueError:
                songs.append({'name': trackName, 'timesPlayed': 1})
        
        eqArtists = {
            # 'Linkin Park': 'Linkin Park+',
            # 'Mike Shinoda': 'Linkin Park+',
            # 'Fort Minor': 'Linkin Park+',
            # 'Dead By Sunrise': 'Linkin Park+',
            # 'Against The Current': 'ATC+',
            # 'Chrissy Costanza': 'ATC+',
            # 'Taka': 'ONE OK ROCK',
            # 'BTS': 'BTS+',
            # 'RM': 'BTS+',
            # 'SUGA': 'BTS+',
            # 'Agust D': 'BTS+',
            # 'Jung Kook': 'BTS+',
            # 'Jimin': 'BTS+',
            # 'j-hope': 'BTS+',
            # 'V': 'BTS+',
            # 'Jin': 'BTS+',
            # 'BLACKPINK': 'BLACKPINK+',
            # 'ROSÉ': 'BLACKPINK+',
            # 'LISA': 'BLACKPINK+',
            # 'JISOO': 'BLACKPINK+',
            # 'JENNIE': 'BLACKPINK+'
        }

        # Track Artists
        if artistStats:
            if type(play['artists']) == list:
                for i, artist in enumerate(play['artists']):
                    if artist in eqArtists.keys():
                        # Ensure don't count artist more than once per song
                        if eqArtists[artist] in [eqArtists[play['artists'][n]] for n in range(i) if play['artists'][n] in eqArtists]: 
                            continue
                        artist = eqArtists[artist]
                    try:
                        index = [d['name'] for d in artists].index(artist)
                        artists[index]['timesPlayed'] += 1
                    except ValueError:
                        artists.append({'name': artist, 'timesPlayed': 1})
            else: 
                if play['artists'] in eqArtists.keys():
                    play['artists'] = eqArtists[play['artists']]
                try:
                    index = [d['name'] for d in artists].index(play['artists'])
                    artists[index]['timesPlayed'] += 1
                except ValueError:
                    artists.append({'name': play['artists'], 'timesPlayed': 1})
    if songStats == False:
        return artists
    elif artistStats == False:
        return songs
    return [songs, artists]

def sortFunc(e):
    return e['timesPlayed']

def top(list: list, prevList=list(), numPlaces=50): 
    list.sort(reverse=True, key=sortFunc)
    prevList.sort(reverse=True, key=sortFunc)
    prevValue = float('inf')
    rank = 1
    for i in range(min(numPlaces, len(list))):
        if prevValue > list[i]['timesPlayed']:
            rank = i+1
            prevValue = list[i]['timesPlayed']
        
        prevComparison = ''
        if prevList:
            try: 
                prevRank = [prev['name'] for prev in prevList].index(list[i]['name'])
            except ValueError:
                prevRank = -1
            
            prevComparison = ' '
            if prevRank > 50 or prevRank == -1:
                prevComparison = '\033[94m·'
            elif prevRank > i:
                prevComparison = '\033[92m↑'
            elif prevRank < i:
                prevComparison = '\033[91m↓'

        print(str(rank), prevComparison, list[i]['name'], list[i]['timesPlayed'], '\033[0m')
        
def topHistory(name: str, isSong: bool, dateRange=timedelta(weeks=24), freq=timedelta(weeks=1), basedOnRank=True):
    history = pd.DataFrame(
        {
            "date": pd.date_range(getStartOfWeek(datetime.now())-dateRange, datetime.now(), freq=freq),
            "position": 50 if basedOnRank else 0
        }
    )
    todayRow = pd.DataFrame([
        {
            "date": datetime.now(),
            "position": 50 if basedOnRank else 0
        }
    ])
    history = pd.concat([history, todayRow], ignore_index=True)
    for i, date in enumerate(history['date']):
        currentStats = getStats(date, timedelta(days=30.43685), songStats=isSong, artistStats=(not isSong))

        if basedOnRank:
            currentStats.sort(reverse=True, key=sortFunc)
            prevValue = float('inf')
            for pos in range(min(50, len(currentStats))):
                if prevValue > currentStats[pos]['timesPlayed']:
                    prevValue = currentStats[pos]['timesPlayed']
                # print(str(rank), artistsNow[pos]['name'], artistsNow[pos]['timesPlayed'])
                if name.lower() in currentStats[pos]['name'].lower():
                    history.loc[i, ['position']] = [pos+1]
        else:
            for pos in range(len(currentStats)):
                if name in currentStats[pos]['name']:
                    history.loc[i, 'position'] = currentStats[pos]['timesPlayed']
                    break

    showPlot(history['date'], history['position'], name, rank=basedOnRank)    

def topNewSongs():
    playlistSongs = ["ONE OK ROCK: Wonder - Japanese Version",
                     "Fujii Kaze: Shinunoga E-Wa",
                     "DAY6: Zombie (English Ver.)",
                     "Oasis: Wonderwall - Remastered",
                     "iann dior: obvious",
                     "Oasis: Champagne Supernova - Remastered",
                     'Weezer: Beginning Of The End - Wyld Stallyns Edit / From The "Bill & Ted Face The Music" Soundtrack',
                     "iann dior: hopeless romantic",
                     "Jex: Where We Started",
                     "Oasis: Don't Look Back In Anger - Remastered",
                     "ONE OK ROCK: Yokubou ni michita seinendan",
                     "Dreamcatcher: Deja Vu",
                     "Depeche Mode: Enjoy The Silence 2004",
                     "Avril Lavigne: Head Above Water",
                     "Mike Shinoda: Place To Start",
                     "Queen: Under Pressure - Remastered 2011",
                     "iann dior: Darkside (feat. Travis Barker)",
                     "Kate Bush: Running Up That Hill (A Deal With God)",
                     "Oasis: Don't Stop… - Demo",
                     "Ninja Sex Party: I Don't Know What We're Talking About (And I Haven't for a While)",
                     "iann dior: Sick and Tired (feat. Machine Gun Kelly & Travis Barker)",
                     "AJR: Location (Recorded at Spotify Studios NYC)",
                     "Bo Burnham: Repeat Stuff (Studio)",
                     "Depeche Mode: It Doesn't Matter",
                     "Mike Shinoda: Place To Start - Remastered",
                     "Depeche Mode: If You Want",
                     "Queen: Bohemian Rhapsody - Remastered 2011",
                     "Depeche Mode: Somebody"]

    newResult = sp.playlist_items(playlist_id='spotify:playlist:7Lp7Bv2OtPB0N4DRRPzrG3')
    offset = 0
    while newResult != None:
        for song in newResult['items']:
            playlistSongs.append(song['track']['artists'][0]['name'] + ": " + song['track']['name'])
        offset += 1
        newResult = sp.next(newResult)
    
    newSongs = [s for s in songs if s['name'].lower() not in [s.lower() for s in playlistSongs]]
    # newSongs = [s for s in songs if s['name'] not in [s for s in playlistSongs]]
    newSongs.sort(reverse=True, key=sortFunc)
    prevValue = float('inf')
    rank = 1
    for i in range(min(50, len(newSongs))):
        if prevValue > newSongs[i]['timesPlayed']:
            rank = i+1
            prevValue = newSongs[i]['timesPlayed']
        
        print(str(rank), newSongs[i]['name'], newSongs[i]['timesPlayed'])        

def findSong(title: str): 
    songs.sort(reverse=True, key=sortFunc)
    for song in songs:
        if title.lower() in song['name'].lower(): 
            print(song['name'], song['timesPlayed'])

def findArtist(name: str): 
    artists.sort(reverse=True, key=sortFunc)
    for artist in artists:
        if name.lower() in artist['name'].lower(): 
            print(artist['name'], artist['timesPlayed'])

def analyzeSongStats():
    newResult = sp.playlist_items(playlist_id='spotify:playlist:3FnTWDOXRaqDQU2r1Q0aG7')
    offset = 0
    playlistArtists = []
    while newResult != None:
        for song in newResult['items']:
            if song['track']['artists'][0]['name'] not in playlistArtists:
                playlistArtists.append(song['track']['artists'][0]['name'])
        offset += 1
        newResult = sp.next(newResult)

    numOfSongs = 0
    for artist in artists:
        if artist['name'] in playlistArtists:
            numOfSongs += artist['timesPlayed']
    print(numOfSongs/sum([s['timesPlayed'] for s in songs]))

def showPlot(x, y, name, rank=True):
    fig,ax = plt.subplots()
    line, = plt.plot(x,y)
    if rank:
        plt.ylim(50, 1)
    plt.title(name)

    # Show annotations
    annot = ax.annotate("", xy=(0,0), xytext=(-20,20),textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w"),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    def update_annot(ind):
        x_data, y_data = line.get_data()
        annot.xy = (x_data[ind["ind"][0]], y_data[ind["ind"][0]])
        # Display the y-value of the hovered point
        text = "x: {}\ny: {:.0f}".format(np.datetime_as_string(x_data[ind["ind"][0]], unit='D'), y_data[ind["ind"][0]])
        annot.set_text(text)
        annot.get_bbox_patch().set_alpha(0.4)

    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            cont, ind = line.contains(event)
            if cont:
                update_annot(ind)
                annot.set_visible(True)
                fig.canvas.draw_idle()
            else:
                if vis:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)
    plt.show()

def getStartOfWeek(dt: datetime) -> datetime:
    return datetime.combine(datetime.date(dt) - timedelta(days=datetime.weekday(dt)), time=datetime.min.time())

# stats = getStats(datetime.utcnow(), timedelta(days=30.43685*2))
# # stats = getStats(datetime.fromisoformat('2024-08-26'), timedelta(days=30.43685))
# songs = stats[0]
# artists = stats[1]
# typeOfAnalysis = st.text_input("Type of analysis: ")
# if typeOfAnalysis == 't':
#     top(songs)
# elif typeOfAnalysis == 'a':
#     top(artists)
# elif typeOfAnalysis == 'sh':
#     topHistory(st.text_input('Artist: ') + ": " + st.text_input('Song: '), isSong=True)
# elif typeOfAnalysis == 'ah':
#     topHistory(st.text_input('Artist: '), isSong=False)
# elif typeOfAnalysis == 'n':
#     topNewSongs()
# elif typeOfAnalysis == 'f':
#     findSong(st.text_input('Song: '))
# elif typeOfAnalysis == 'fa':
#     findArtist(st.text_input('Artist: '))
# elif typeOfAnalysis == 'g':
#     analyzeSongStats()


if __name__ == "__main__":
    main()