import pandas as pd
from math import ceil
from data.data_loader import (
    load_experiment_runs,
    load_experiment_sums,
    load_project_experiments,
    load_run_emissions,
    load_run_sums,
)

# from data_loader import load_run_emissions, load_project_experiments, load_experiment_runs, load_experiment_sums, load_run_sums


def get_run_data(run_id, page_api, size_api) -> pd.DataFrame:
    run_from_api = load_run_emissions(run_id, page=page_api, size=size_api)
    run_df = pd.DataFrame(run_from_api["items"])
    if not (run_df.empty):
        run_df = run_df.sort_values(by="timestamp")
    run_total = run_from_api["total"]
    return run_df, run_total


# run_name = '27ce2e82-7ffc-4c45-8967-8af041b29a00'
# df, total = get_run_data(run_name,1,10000)
# print(df.iloc[:5,:3], '\n\nRun_data :', df.shape, '\n\nTotal :', total)


def get_run_emissions(run_id, size=10000) -> pd.DataFrame:
    run_df, run_total = get_run_data(run_id, 1, size)
    max_page = ceil(run_total / size)
    for i in list(range(max_page - 1)):
        run_page_i, total_i = get_run_data(run_id, i + 2, size)
        run_df = pd.concat([run_page_i, run_df], ignore_index=True)
    return run_df, run_total


# run_name = '58e2c11e-b91f-4adb-b0e0-7e91b72ffb80'
# df, total = get_run_emissions(run_name)
# print(df.iloc[:5,:3], '\n', df.iloc[total-5:,:3], '\n\nRun_data :', df.shape, '\n\nTotal :', total)


def get_project_experiments(project_id):
    dict = load_project_experiments(project_id)
    df = pd.DataFrame.from_dict(dict)
    if not (df.empty):
        df = df.sort_values(by="timestamp")
    return df


# project_name = '225904ca-f741-477c-83f5-d61587d6286c'
# print(get_project_experiments(project_name)['id'][0])


def get_experiment_runs(experiment_id):
    dict = load_experiment_runs(experiment_id)
    df = pd.DataFrame.from_dict(dict)
    if not (df.empty):
        df = df.sort_values(by="timestamp")
    return df


# experiment_id = '0bfa2432-efda-4656-bdb4-f72d15866b0b'
# print(get_experiment_runs(experiment_id)['id'][0])


def get_experiment_sums(project_id, date_from, date_to):
    dict = load_experiment_sums(project_id, start_date=date_from, end_date=date_to)
    df = pd.DataFrame.from_dict(dict)
    if not (df.empty):
        df = df.sort_values(by="timestamp")
    return df


# project_name = 'e60afa92-17b7-4720-91a0-1ae91e409ba1'
# print(get_experiment_sums(project_name))


def get_run_sums(experiment_id, date_from, date_to):
    dict = load_run_sums(experiment_id, start_date=date_from, end_date=date_to)
    df = pd.DataFrame.from_dict(dict)
    if not (df.empty):
        df = df.sort_values(by="timestamp")
    return df


# experiment_id = '0bfa2432-efda-4656-bdb4-f72d15866b0b'
# print(get_run_sums(experiment_id,'2020-01-01 00:00:00','2022-01-01 00:00:00'))