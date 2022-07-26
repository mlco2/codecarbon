"""
API functions
"""


from math import ceil

import pandas as pd
from data.data_loader import *


def get_run_data(run_id, page_api, size_api) -> pd.DataFrame:
    run_from_api = load_run_emissions(run_id, page=page_api, size=size_api)
    run_df = pd.DataFrame(run_from_api["items"])
    if not (run_df.empty):
        run_df = run_df.sort_values(by="timestamp")
    run_total = run_from_api["total"]
    return run_df, run_total


def get_run_info(run_id) -> pd.DataFrame:
    run_from_api = load_run_infos(run_id)
    col = [
        "os",
        "python_version",
        "cpu_count",
        "cpu_model",
        "gpu_count",
        "gpu_model",
        "longitude",
        "latitude",
        "region",
        "provider",
        "ram_total_size",
        "tracking_mode",
    ]
    filtered_d = dict((k, run_from_api[k]) for k in col if k in run_from_api)

    return filtered_d


def get_run_emissions(run_id, size=10000) -> pd.DataFrame:
    run_df, run_total = get_run_data(run_id, 1, size)
    max_page = ceil(run_total / size)
    for i in list(range(max_page - 1)):
        run_page_i, total_i = get_run_data(run_id, i + 2, size)
        run_df = pd.concat([run_page_i, run_df], ignore_index=True)
    return run_df, run_total


def get_project_experiments(project_id) -> pd.DataFrame:
    dict = load_project_experiments(project_id)
    df = pd.DataFrame.from_dict(dict)
    if not (df.empty):
        df = df.sort_values(by="timestamp")
    return df


def get_experiment_runs(experiment_id, date_from, date_to) -> pd.DataFrame:
    dict = load_experiment_runs(experiment_id)
    df = pd.DataFrame.from_dict(dict)
    if not (df.empty):
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df[(df["timestamp"] >= date_from) & (df["timestamp"] <= date_to)]
        df = df.sort_values(by="timestamp")
    return df


def get_experiment_sums(project_id, date_from, date_to) -> pd.DataFrame:
    dict = load_experiment_sums(project_id, start_date=date_from, end_date=date_to)
    df = pd.DataFrame.from_dict(dict)
    if not (df.empty):
        df = df.sort_values(by="timestamp")
    return df


def get_run_sums(experiment_id, date_from, date_to) -> pd.DataFrame:
    dict = load_run_sums(experiment_id, start_date=date_from, end_date=date_to)
    df = pd.DataFrame.from_dict(dict)
    if not (df.empty):
        df = df.sort_values(by="timestamp")
    return df


def get_project_sums(project_id, date_from, date_to) -> tuple:
    dict = load_project_sums(project_id, start_date=date_from, end_date=date_to)
    return dict


def get_orga_sums(organization_id, date_from, date_to) -> tuple:
    dict = load_orga_sums(organization_id, start_date=date_from, end_date=date_to)
    return dict


def get_experiment(experiment_id) -> tuple:
    dict = load_experiment(experiment_id)
    return dict


def get_project(project_id) -> tuple:
    dict = load_project(project_id)
    return dict


def get_lastrun(project_id, date_from, date_to) -> tuple:
    dict = load_lastrun(project_id, start_date=date_from, end_date=date_to)
    return dict


def get_organization_list() -> pd.DataFrame:
    return pd.DataFrame.from_dict(load_organizations())


def get_project_list(organization_id) -> pd.DataFrame:
    teams = pd.DataFrame.from_dict(load_organization_teams(organization_id))
    projects = pd.DataFrame(columns=["name", "id"])
    if len(teams) == 0:
        return projects
    for i in teams["id"]:
        projects_to_add = pd.DataFrame.from_dict(load_team_projects(i))
        projects = pd.concat([projects, projects_to_add])
    return projects
