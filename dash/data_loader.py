import requests
import pandas as pd
from settings import API_PATH, USER, PSSD

def load_data_from_csv():
    return pd.read_csv('api_extract.csv', parse_dates=['timestamp'])


def load_from_api(experiment_id):
    """
    Load data from API

    :note:
        Only implemented at experiment granularity
        Sample test using experiment_id='3a202149-8be2-408c-a3d8-baeae2de2987'
    """
    request_path = API_PATH + 'experiment/' + experiment_id
    r = requests.get(request_path, auth=(USER, PSSD))
    return r.content
