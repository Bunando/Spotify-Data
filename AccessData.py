import subprocess
import json

def getData():
    # Running a shell command and capturing its output
    result = json.loads(subprocess.run(['docker', 'exec', '-it', '22ab5671e609', 'cat', 'SelfCollectedData.json'], capture_output=True, text=True).stdout)
    return result

def pullData(): 
    subprocess.run(['docker', 'cp', '22ab5671e609:/usr/local/airflow/SelfCollectedData.json', './Airflow'])

def pushData(): 
    subprocess.run(['docker', 'cp', '/Airflow/SelfCollectedData.json', '22ab5671e609:/usr/local/airflow'])
    subprocess.run(['docker', 'exec', '-it', '--user', 'root', '22ab5671e609', 'chown', '-R', 'astro:astro', 'SelfCollectedData.json'])

if __name__ == "__main__":
    # pullData()
    pass