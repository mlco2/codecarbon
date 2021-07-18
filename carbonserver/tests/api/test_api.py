import os
import random

import pytest
import requests

# Get the API utl to use from an env variable if exist
URL = os.getenv("CODECARBON_API_URL")
if URL is None:
    pytest.exit("CODECARBON_API_URL is not defined")

experiment_id = project_id = user_id = api_key = org_id = team_id = email = None
org_name = org_description = org_new_id = None
team_name = team_description = team_new_id = emission_id = None
password = "Secret1!îstring"


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
    email = f"test-{random.randint(1, 20_000_000)}@test.com"
    payload = {"email": email, "name": "toto", "password": password}
    r = requests.post(url=URL + "/user", json=payload, timeout=2)
    assert r.status_code == 201
    assert r.json()["email"] == email
    assert r.json()["is_active"] == True  # noqa


def test_api_user_signup():
    global user_id, api_key, org_id, team_id, email
    email = f"test-{random.randint(1, 20_000_000)}@test.com"
    payload = {"email": email, "name": "toto", "password": password}
    r = requests.post(url=URL + "/user/signup/", json=payload, timeout=2)
    assert r.status_code == 201
    assert r.json()["email"] == email
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
    assert r.json()["email"] == email


def test_api_auth_success():
    payload = {"email": email, "password": password}
    r = requests.post(url=URL + "/authenticate/", json=payload, timeout=2)
    assert r.status_code == 200
    assert r.json()["access_token"] == "a"
    assert r.json()["token_type"] == "access"


def test_api_auth_fail():
    payload = {"email": "toto@free.fr", "password": "password"}
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
    assert r.json()[1]["id"] == org_id


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
    assert is_key_value_exist(r.json(), "id", team_id)


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


@pytest.mark.xfail(reason="Not implemented yet")
def test_api_projects_list():
    r = requests.get(url=URL + "/projects", timeout=2)
    assert r.status_code == 200
    assert is_key_value_exist(r.json(), "id", project_id)


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
    payload = {"timestamp": "2021-04-04T08:43:00+02:00", "experiment_id": experiment_id}
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


def test_api_emission_create():
    payload = {
        "timestamp": "2021-04-04T08:43:00+02:00",
        "run_id": run_id,
        "duration": 42,
        "emissions": 487956487.654,
        "energy_consumed": 8794512.6547,
    }
    r = requests.post(url=URL + "/emission/", json=payload, timeout=2)
    assert r.status_code == 201


def test_api_emission_list():
    global emission_id
    r = requests.get(url=URL + "/emissions/run/" + run_id, timeout=2)
    assert r.status_code == 200
    assert is_key_all_values_equal(r.json(), "run_id", run_id)
    emission_id = r.json()[-1]["id"]


def test_api_emission_read():
    r = requests.get(url=URL + "/emission/" + emission_id, timeout=2)
    assert r.status_code == 200
    assert r.json()["id"] == emission_id
    assert r.json()["run_id"] == run_id
