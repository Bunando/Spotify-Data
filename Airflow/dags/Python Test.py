from airflow.decorators import dag, task
from airflow.models import Variable
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth

@dag(
    start_date=datetime(2023, 1, 1),
    schedule='@daily',
    tags=['activity'],
    catchup=False,
)
def python_test():
    @task
    def test_function():
        return 2*2
    
    @task
    def write_value_to_file(response): 
        filepath = Variable.get('recently_played_file')
        with open(filepath, "a") as f:
            f.write(f'Today you will: {response}') 
        return filepath
    
    @task
    def read_value_from_file(filepath):
        with open(filepath, 'r') as f:
            print(f.read())

    response = test_function()
    filepath = write_value_to_file(response)
    read_value_from_file(filepath)

python_test()