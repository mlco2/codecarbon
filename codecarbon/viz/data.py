from typing import Dict, List, Tuple

import dash_table as dt
import pandas as pd

from codecarbon.core.emissions import Emissions
from codecarbon.input import DataSource, DataSourceException

from codecarbon.viz.data_loader import load_emission

class Data:
    def __init__(self):
        self._data_source = DataSource()
        self._emissions = Emissions(self._data_source)

    @staticmethod
    def get_run_data(run_id) -> dt.DataTable:
        run_from_api = load_emission(run_id)
        run_df = pd.DataFrame(run_from_api['items'])

        run_df = run_df.sort_values(by="timestamp")
        run_data = run_df.to_dict("records")
        columns = [{"name": column, "id": column} for column in run_df.columns]
        return dt.DataTable(data=run_data, columns=columns)

    @staticmethod
    def get_run_summary(run_data: List[Dict]):
        last_emission = run_data[-1]
        run_summary = {
            "last_emission": {
                "timestamp": last_emission["timestamp"],
                "duration": last_emission["duration"],
                "emissions": round(last_emission["emissions_sum"], 1),
                "energy_consumed": round((last_emission["energy_consumed"]), 1),
            },
        }
        return run_summary
