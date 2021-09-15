import json
import requests

API_PATH = "http://api.codecarbon.io"
USER = "jessica"
PSSD = "fake-super-secret-token"

def api_loader(fn_request_path):
    def wrapper(*args, **kwargs):
        r_path = fn_request_path(*args, **kwargs)
        r = requests.get(r_path, auth=(USER, PSSD))
        c = json.loads(r.content)
        return c
    return wrapper


@api_loader
def load_runs():
    return f"{API_PATH}/runs"


@api_loader
def load_project_experiments(project_id):
    """Test project_id = 'e60afa92-17b7-4720-91a0-1ae91e409ba1'"""
    return f"{API_PATH}/experiments/project/{project_id}"


@api_loader
def load_experiment(experiment_id):
    """Test experiment_id = '3a202149-8be2-408c-a3d8-baeae2de2987'"""
    # 0bfa2432-efda-4656-bdb4-f72d15866b0b
    return f"{API_PATH}/experiment/{experiment_id}"


# Not Found
@api_loader
def load_organization_teams(organization_id):
    """Test organization_id = 'e52fe339-164d-4c2b-a8c0-f562dfce066d'"""
    return f"{API_PATH}/teams/organization/{organization_id}"


# Not Found
@api_loader
def load_team_projects(team_id):
    """Test team_id = 'c13e851f-5c2f-403d-98d0-51fe15df3bc3'"""
    return f"{API_PATH}/projects/team/{team_id}"


# Not Found
@api_loader
def load_experiment_runs(experiment_id):
    """Test experiment_id = 'f52fe339-164d-4c2b-a8c0-f562dfce066d'"""
    return f"{API_PATH}/runs/experiment/{experiment_id}"


@api_loader
def load_emission(run_id):
    """Test run_id = '58e2c11e-b91f-4adb-b0e0-7e91b72ffb80'"""
    return f"{API_PATH}/emissions/run/{run_id}"
