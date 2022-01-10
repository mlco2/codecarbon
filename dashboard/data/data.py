from math import ceil

import pandas as pd
from data.data_loader import load_run_emissions


def get_run_data(run_id, page_api, size_api) -> pd.DataFrame:
    run_from_api = load_run_emissions(run_id, page=page_api, size=size_api)
    run_df = pd.DataFrame(run_from_api["items"])
    # SORT RUN DATA BY TIMESTAMP
    run_df = run_df.sort_values(by="timestamp")
    run_total = run_from_api["total"]
    return run_df, run_total


# run_name = '27ce2e82-7ffc-4c45-8967-8af041b29a00'
# df, total = get_run_data(run_name,1,10000)
# print(df.iloc[:5,:3], '\n\nRun_data :', df.shape, '\n\nTotal :', total)


def get_concat_run_data(run_id, size=10000) -> pd.DataFrame:
    run_df, run_total = get_run_data(run_id, 1, size)
    max_page = ceil(run_total / size)
    for i in list(range(max_page - 1)):
        run_page_i, total_i = get_run_data(run_id, i + 2, size)
        # CONCAT AND SORT RUN DATA BY TIMESTAMP
        run_df = pd.concat([run_page_i, run_df], ignore_index=True)
    return run_df, run_total


# run_name = '58e2c11e-b91f-4adb-b0e0-7e91b72ffb80'
# df, total = get_concat_run_data(run_name)
# print(df.iloc[:5,:3], '\n', df.iloc[total-5:,:3], '\n\nRun_data :', df.shape, '\n\nTotal :', total)
