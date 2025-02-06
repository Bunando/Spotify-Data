import json
from datetime import datetime
from datetime import timedelta
import os
import spotipy
from spotipy import SpotifyClientCredentials
from JSONEncoder import CompactListJSONEncoder
from dotenv import load_dotenv

load_dotenv()

def main():
    data = list()

    try:
        with open('AllData.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []
        if input('Create New File? ') != 'y':
            raise FileNotFoundError
        
    def sortFunc(e):
        return int(e.split('_')[-1].split('.')[0]) # Change depending on file naming convention

    results = []
    for filepath in sorted(os.listdir('History To Add'), key=sortFunc):
        f = os.path.join('History To Add', filepath)
        print(f)
        with open(f, 'r', encoding='utf-8') as file:
            results.extend(json.load(file))

    auth_manager = SpotifyClientCredentials()
    sp = spotipy.Spotify(auth_manager=auth_manager, retries=0)
    tracksToRequest = []
    trackDetails = []
    for i, play in enumerate(results):
        if play['master_metadata_track_name'] == None:
            continue
        endTime = datetime.fromisoformat(play['ts'])
        endTime = datetime.fromisoformat(f"{endTime.date()} {str(endTime.hour).zfill(2)}:{str(endTime.minute).zfill(2)}:{str(int(endTime.second)).zfill(2)}")
        if len(data) != 0 and (endTime - datetime.fromisoformat(data[-1]['endTime'])) < timedelta(seconds=0):
            print(play['master_metadata_album_artist_name'] + ": " + play['master_metadata_track_name'], endTime, play['ms_played'])
            print('Skipped')
            continue
        
        trackDetails.append({'endTime': str(endTime),
                            'msPlayed': play['ms_played']})
        
        tracksToRequest.append(play['spotify_track_uri'].split(':')[2])

        if len(tracksToRequest) == 50 or i == len(results)-1:
            print(str(round((i+1)/len(results)*100, 2)) + "%")
            tracks = sp.tracks(tracksToRequest)
            for n, track in enumerate(tracks['tracks']):
                data.append({'endTime': trackDetails[n]['endTime'], 
                            'artists': [artist['name'] for artist in track['artists']],
                            'trackName': track['name'],
                            'msPlayed': trackDetails[n]['msPlayed']})
            tracksToRequest = []
            trackDetails = []
            

    with open('AllData.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=CompactListJSONEncoder)

    

if __name__ == '__main__':
    main()