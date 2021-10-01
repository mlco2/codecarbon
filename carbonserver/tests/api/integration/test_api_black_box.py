import os

import pytest
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from carbonserver.config import settings

# Get the API utl to use from an env variable if exist
URL = os.getenv("CODECARBON_API_URL")
if URL is None:
    pytest.exit("CODECARBON_API_URL is not defined")

experiment_id = project_id = user_id = api_key = org_id = team_id = None
org_name = org_description = org_new_id = None
team_name = team_description = team_new_id = emission_id = None
USER_PASSWORD = "Secret1!îstring"
USER_EMAIL = "user@integration.test"


# @pytest.fixture()
def del_test_user():
    """Fixture to destroy user"""
    engine = create_engine(settings.db_url)  #
    stmt = text("DELETE FROM users WHERE email=:email").bindparams(email=USER_EMAIL)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()
    # Clean up user before ending test execution by pytest
    # delete(SqlModelUser).where(SqlModelUser.email == USER_EMAIL)


def is_key_value_exist(list_of_dict, key, value):
    """
    Check if at least one value of a key is equal to the specified value.
    """
    for d in list_of_dict:
        if d[key] == value:
            return True
    return False


def is_key_all_values_equal(list_of_dict, key, value):
    """
    Check if all values of a key are equal to the specified value.
    """
    for d in list_of_dict:
        if d[key] != value:
            return False
    return True


def test_api_user_create():
    assert URL is not None
    # we delete it if exist
    del_test_user()
    payload = {"email": USER_EMAIL, "name": "toto", "password": USER_PASSWORD}
    r = requests.post(url=URL + "/user", json=payload, timeout=2)
    assert r.status_code == 201
    assert r.json()["email"] == USER_EMAIL
    assert r.json()["is_active"] == True  # noqa


def test_api_user_signup():
    global user_id, api_key, org_id, team_id
    # signup is creating a user, we delete it if exist
    del_test_user()
    payload = {"email": USER_EMAIL, "name": "toto", "password": USER_PASSWORD}
    r = requests.post(url=URL + "/user/signup/", json=payload, timeout=2)
    assert r.status_code == 201
    assert r.json()["email"] == USER_EMAIL
    assert r.json()["is_active"] == True  # noqa
    user_id = r.json()["id"]
    api_key = r.json()["api_key"]
    org_id = r.json()["organizations"][0]
    team_id = r.json()["teams"][0]


def test_api_users_list():
    r = requests.get(url=URL + "/users", timeout=2)
    assert r.status_code == 200
    assert is_key_value_exist(r.json(), "id", user_id)


def test_api_get_user():
    r = requests.get(url=URL + "/user/" + user_id, timeout=2)
    assert r.status_code == 200
    assert r.json()["id"] == user_id
    assert r.json()["email"] == USER_EMAIL


def test_api_auth_success():
    payload = {"email": USER_EMAIL, "password": USER_PASSWORD}
    r = requests.post(url=URL + "/authenticate/", json=payload, timeout=2)
    assert r.status_code == 200
    assert r.json()["access_token"] == "a"
    assert r.json()["token_type"] == "access"


def test_api_auth_wrong_email():
    payload = {
        "email": "long.user.email.that.cant.exist.3495739@asdfijvneurvbier.fr",
        "password": USER_PASSWORD,
    }
    r = requests.post(url=URL + "/authenticate/", json=payload, timeout=2)
    assert r.status_code == 401


def test_api_auth_wrong_password():
    payload = {"email": USER_EMAIL, "password": "wrong-password"}
    r = requests.post(url=URL + "/authenticate/", json=payload, timeout=2)
    assert r.status_code == 401


def test_api_user_deleted():
    del_test_user()
    payload = {"email": USER_EMAIL, "password": USER_PASSWORD}
    r = requests.post(url=URL + "/authenticate/", json=payload, timeout=2)
    assert r.status_code == 401


def test_api_organization_create():
    global org_name, org_description, org_new_id
    org_name = "test_to_delete"
    org_description = "test to delete"
    payload = {"name": org_name, "description": org_description}
    r = requests.post(url=URL + "/organization", json=payload, timeout=2)
    assert r.status_code == 201
    assert r.json()["name"] == org_name
    assert r.json()["description"] == org_description
    org_new_id = r.json()["id"]


def test_api_organization_read():
    r = requests.get(url=URL + "/organization/" + org_new_id, timeout=2)
    assert r.status_code == 200
    assert r.json()["name"] == org_name
    assert r.json()["description"] == org_description


def test_api_organization_list():
    r = requests.get(url=URL + "/organizations", timeout=2)
    assert r.status_code == 200
    assert r.json()[-1]["id"] == org_new_id


def test_api_team_create():
    global team_name, team_description, team_new_id
    team_name = "test_to_delete"
    team_description = "test to delete"
    payload = {
        "name": team_name,
        "description": team_description,
        "organization_id": org_new_id,
        "api_key": api_key,
    }
    r = requests.post(url=URL + "/team", json=payload, timeout=2)
    assert r.status_code == 201
    assert r.json()["name"] == team_name
    assert r.json()["description"] == team_description
    team_new_id = r.json()["id"]


def test_api_team_read():
    r = requests.get(url=URL + "/team/" + team_new_id, timeout=2)
    assert r.status_code == 200
    assert r.json()["name"] == team_name
    assert r.json()["description"] == team_description


def test_api_teams_list():
    r = requests.get(url=URL + "/teams", timeout=2)
    assert r.status_code == 200
    assert is_key_value_exist(r.json(), "id", team_new_id)


def test_api_teams_for_organization_list():
    r = requests.get(url=URL + "/teams/organization/" + org_new_id, timeout=2)
    assert r.status_code == 200
    assert is_key_value_exist(r.json(), "id", team_new_id)
    assert is_key_all_values_equal(r.json(), "organization_id", org_new_id)


def test_api_project_create():
    global project_id
    payload = {
        "name": "test_to_delete",
        "description": "Test to delete",
        "team_id": team_new_id,
    }
    r = requests.post(url=URL + "/project/", json=payload, timeout=2)
    assert r.status_code == 201
    assert r.json()["team_id"] == team_new_id
    project_id = r.json()["id"]


def test_api_projects_for_team_list():
    r = requests.get(url=URL + "/projects/team/" + team_new_id, timeout=2)
    assert r.status_code == 200
    assert is_key_value_exist(r.json(), "id", project_id)
    assert is_key_all_values_equal(r.json(), "team_id", team_new_id)


def test_api_experiment_create():
    global experiment_id
    payload = {
        "name": "Run on Premise",
        "description": "Premise API for Code Carbon",
        "timestamp": "2021-04-04T08:43:00+02:00",
        "country_name": "France",
        "country_iso_code": "FRA",
        "region": "france",
        "on_cloud": True,
        "cloud_provider": "Premise",
        "cloud_region": "eu-west-1a",
        "project_id": project_id,
    }
    r = requests.post(url=URL + "/experiment", json=payload, timeout=2)
    assert r.status_code == 201
    assert r.json()["project_id"] == project_id
    experiment_id = r.json()["id"]


def test_api_experiment_read():
    r = requests.get(url=URL + "/experiment/" + experiment_id, timeout=2)
    assert r.status_code == 200
    assert r.json()["id"] == experiment_id


def test_api_experiment_list():
    r = requests.get(url=URL + "/experiments/project/" + project_id, timeout=2)
    assert r.status_code == 200
    assert is_key_value_exist(r.json(), "id", experiment_id)


def test_api_run_create():
    global run_id
    payload = {
        "timestamp": "2021-04-04T08:43:00+02:00",
        "experiment_id": experiment_id,
        "os": "macOS-10.15.7-x86_64-i386-64bit",
        "python_version": "3.8.0",
        "cpu_count": 12,
        "cpu_model": "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz",
        "gpu_count": 4,
        "gpu_model": "NVIDIA",
        "longitude": -7.6174,
        "latitude": 33.5822,
        "region": "EUROPE",
        "provider": "AWS",
        "ram_total_size": 83948.22,
        "tracking_mode": "Machine",
    }
    r = requests.post(url=URL + "/run/", json=payload, timeout=2)
    assert r.status_code == 201
    run_id = r.json()["id"]


def test_api_run_read():
    r = requests.get(url=URL + "/run/" + run_id, timeout=2)
    assert r.status_code == 200
    assert r.json()["id"] == run_id


def test_api_run_list():
    r = requests.get(url=URL + "/runs", timeout=2)
    assert r.status_code == 200
    assert is_key_value_exist(r.json(), "id", run_id)


def test_api_runs_for_team_list():
    r = requests.get(url=URL + "/runs/experiment/" + experiment_id, timeout=2)
    assert r.status_code == 200
    assert is_key_value_exist(r.json(), "id", run_id)
    assert is_key_all_values_equal(r.json(), "experiment_id", experiment_id)


def test_api_emission_create():
    payload = {
        "timestamp": "2021-04-04T08:43:00+02:00",
        "run_id": run_id,
        "duration": 98745,
        "emissions_sum": 1544.54,
        "emissions_rate": 1.548444,
        "cpu_power": 0.3,
        "gpu_power": 10.65,
        "ram_power": 1.15,
        "cpu_energy": 55.21874,
        "gpu_energy": 106540.65484,
        "ram_energy": 64.654688,
        "energy_consumed": 57.21874,
    }
    r = requests.post(url=URL + "/emission/", json=payload, timeout=2)
    assert r.status_code == 201


def test_api_emission_list():
    global emission_id
    r = requests.get(url=URL + "/emissions/run/" + run_id, timeout=2)
    assert r.status_code == 200
    assert is_key_all_values_equal(r.json()["items"], "run_id", run_id)
    emission_id = r.json()["items"][-1]["id"]


def test_api_emission_read():
    r = requests.get(url=URL + "/emission/" + emission_id, timeout=2)
    assert r.status_code == 200
    assert r.json()["id"] == emission_id
    assert r.json()["run_id"] == run_id
