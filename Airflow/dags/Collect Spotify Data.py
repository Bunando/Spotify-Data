from airflow.decorators import dag, task
from airflow.models import Variable
from datetime import datetime, timedelta, timezone
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

# # fix for mac machines
# import os
# import _scproxy
# _scproxy._get_proxy_settings()  # run before forking
# os.environ['NO_PROXY'] = '*'

@dag(
    start_date=datetime(2024, 9, 7),
    schedule=timedelta(hours=2),
    tags=['collect'],
    catchup=False,
    default_args={
        'retries': 1
    }
)
def collect_spotify_data():
    @task
    def api_request():
        scope = "user-read-recently-played"

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(redirect_uri="http://localhost:1234",
                                                    scope=scope),
                            retries=0)
        
        results = sp.current_user_recently_played(limit=50)
        return results

    @task
    def find_file():
        filepath = Variable.get('self_collected_data')
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    @task(multiple_outputs=True)
    def add_songs_to_data(data, results):
        missedData = timedelta()
        firstResult = True
        for result in results['items'][::-1]:
            # Format endTime correctly
            endTime = datetime.fromisoformat(result['played_at'])
            endTime = endTime.replace(tzinfo=None)
            # endTime = datetime.fromisoformat(f"{endTime.date()} {str(endTime.hour).zfill(2)}:{str(endTime.minute).zfill(2)}:{str(endTime.second).zfill(2)}.{str(int(endTime.microsecond/1000)).zfill(3)}")

            # Calculate amount of time song was played
            msPlayed = timedelta(milliseconds=result['track']['duration_ms'])
            if endTime - datetime.fromisoformat(data[-1]['endTime']) < msPlayed:
                msPlayed = endTime - datetime.fromisoformat(data[-1]['endTime'])

            # Skip track if played less than 30 seconds
            print(result['track']['artists'][0]['name'] + ": " + result['track']['name'], endTime, result['track']['duration_ms'])
            if len(data) != 0 and msPlayed < timedelta(seconds=30):
                print('Skipped')
                firstResult = False
                continue

            if firstResult:
                missedData = endTime - datetime.fromisoformat(data[-1]['endTime'])
            
            endTimeStr = str(endTime)
            if endTime.microsecond != 0:
                endTimeStr = str(endTime.replace(microsecond=0)) + '.' + str(int(endTime.microsecond/1000)).zfill(3)
                        
            data.append({'endTime' : endTimeStr, 
                        'artists': [artist['name'] for artist in result['track']['artists']],
                        'trackName': result['track']['name'],
                        'msPlayed': int(msPlayed.total_seconds()*1000)})
            firstResult = False
        
        return {'data': data, 'missedData': missedData}

    @task
    def write_data_to_file(data): 
        filepath = Variable.get('self_collected_data')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=CompactListJSONEncoder)
        return filepath
    
    @task
    def track_missed_data(missedData):
        if missedData != timedelta():
            print("Missed data: ", missedData)
            with open("data/missedData.txt", 'a') as f:
                f.write(str(datetime.now()) + ", " + str(missedData))
                f.write("\n")
        else:
            print("No missed data")
    
    @task
    def create_file():
        filepath = Variable.get("self_collected_data")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return filepath
    
    results = api_request()
    fileData = find_file()
    data = add_songs_to_data(fileData, results)
    write_data_to_file(data['data'])
    track_missed_data(data['missedData'])
    # create_file()

class CompactListJSONEncoder(json.JSONEncoder):
    def iterencode(self, obj, _one_shot=False):
        if isinstance(obj, list):
            # Handle lists of dictionaries with proper indentation but no extra newlines between items
            if all(isinstance(el, dict) for el in obj):
                return '[\n' + ',\n'.join('  ' + self.encode(el) for el in obj) + '\n]'
            # For other lists, keep them compact on one line
            return '[' + ', '.join(self.encode(el) for el in obj) + ']'
        elif isinstance(obj, dict):
            # For dictionaries, ensure proper indentation for keys/values and closing braces
            items = ['"{}": {}'.format(k, self.encode(v)) for k, v in obj.items()]
            return '{\n' + ',\n'.join('    ' + item for item in items) + '\n  }'
        return super().iterencode(obj, _one_shot)

collect_spotify_data()