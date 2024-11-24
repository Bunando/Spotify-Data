import json
from datetime import datetime
from datetime import timedelta
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth

scope = "user-read-recently-played"

def collectData():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="49e5d067614c4d3e8e2dd2335cbaf4e0",
                                            client_secret="6546b49cbce74e3fb690829c45b86c1b",
                                            redirect_uri="http://localhost:1234",
                                            scope=scope))
    # sp = spotipy.Spotify(auth="BQBRKzH9tcWb-5m3wcsZ68sYrhqktpspVr_2tjSDGvpMKNjb49HcT9HBcxUsJncXBuVi5VrpFSjkPgSnmiTBeLStThNtcD7TvP5MXR0VWO_eqlDcoS1ewo7gF_PDTTLVAsbSrLsQpwjFea8jrufcP6W5ea1F71SGv_aoFOI801xNOampwN7CJj0f93nSkkxnAZTxjdukYlyUn2CU4RI")
    
    results = sp.current_user_recently_played(limit=50)

    try:
        with open('SelfCollectedData.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []
        if input('Create New File? ') != 'y':
            raise FileNotFoundError

    for result in results['items'][::-1]:
        endTime = datetime.fromisoformat(result['played_at'])
        endTime = datetime.fromisoformat(f"{endTime.date()} {str(endTime.hour).zfill(2)}:{str(endTime.minute).zfill(2)}:{str(int(endTime.second)).zfill(2)}")
        print(result['track']['artists'][0]['name'] + ": " + result['track']['name'], endTime, result['track']['duration_ms'])
        if len(data) != 0 and (endTime - datetime.fromisoformat(data[-1]['endTime'])) < timedelta(seconds=30):
            print('Skipped')
            continue

        data.append({'endTime' : str(endTime), 
                    'artistName': result['track']['artists'][0]['name'],
                    'trackName': result['track']['name'],
                    'msPlayed': result['track']['duration_ms']})

    with open('SelfCollectedData.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    while True:
        collectData()
        time.sleep(60*120)
        print()

if __name__ == '__main__':
    main()