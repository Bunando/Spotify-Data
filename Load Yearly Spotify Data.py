import json
from datetime import datetime
from datetime import timedelta
import spotipy
from spotipy import SpotifyClientCredentials
from JSONEncoder import CompactListJSONEncoder

# Get last date from AllData
lastDate = datetime.min
try:
    with open('AllData.json', 'r', encoding='utf-8') as file:
        allData = json.load(file)
        lastDate = datetime.fromisoformat(allData[-1]['endTime'])
except FileNotFoundError:
    pass

try:
    with open('PastYearData.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        if data != [] and datetime.fromisoformat(data[-1]['endTime']) > lastDate:
            lastDate = datetime.fromisoformat(data[-1]['endTime'])
except FileNotFoundError:
    data = []
    if input('Create New File? ') != 'y':
        raise FileNotFoundError


with open('StreamingHistory_music_3.json', 'r', encoding='utf-8') as file:
    newData = json.load(file)

auth_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager, retries=0)

for i, play in enumerate(newData):
    endTime = datetime.fromisoformat(play['endTime'])
    if endTime <= lastDate:
        print("Skipped: " + play['artistName'] + ": " + play['trackName'], endTime, play['msPlayed'])
        continue
    
    print(str(round((i+1)/len(newData)*100, 2)) + "%")
    song = sp.search("track:" + play['trackName'] + " artist:" + play['artistName'], limit=1, type='track')

    data.append({'endTime': play['endTime'], 
                'artists': [artist['name'] for artist in song['tracks']['items'][0]['artists']],
                'trackName': play['trackName'],
                'msPlayed': play['msPlayed']})
    
    # data.append({'endTime': play['endTime'], 
    #             'artists': [play['artistName']],
    #             'trackName': play['trackName'],
    #             'msPlayed': play['msPlayed']})

with open('PastYearData.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2, cls=CompactListJSONEncoder)