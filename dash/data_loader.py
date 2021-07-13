import pandas as pd

def load_data():
    return pd.read_csv('api_extract.csv', parse_dates=['timestamp'])
