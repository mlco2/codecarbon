import random

import requests

URL = "http://localhost:8008"
experiment_id = project_id = user_id = api_key = org_id = team_id = email = None
password = "Secret1!îstring"


def test_create():
    global user_id, api_key, org_id, team_id, email
    email = f"test-{random.randint(1, 1000)}@test.com"
    payload = {"email": email, "name": "toto", "password": password}
    r = requests.post(url=URL + "/users/signup/", json=payload, timeout=2)
    print(r.json())
    assert r.status_code == 201
    assert r.json()["email"] == email
    assert r.json()["is_active"] == True  # noqa
    user_id = r.json()["id"]
    api_key = r.json()["api_key"]
    org_id = r.json()["organizations"][0]
    team_id = r.json()["teams"][0]


def test_auth_success():
    payload = {"email": email, "password": password}
    r = requests.post(url=URL + "/authenticate/", json=payload, timeout=2)
    print(r.json())
    assert r.status_code == 200
    assert r.json()["access_token"] == "a"
    assert r.json()["token_type"] == "access"


def test_auth_fail():
    payload = {"email": "toto@free.fr", "password": "password"}
    r = requests.post(url=URL + "/authenticate/", json=payload, timeout=2)
    print(r.json())
    assert r.status_code == 401


def test_list_organizations():
    r = requests.get(url=URL + "/organizations/", timeout=2)
    assert r.status_code == 200
    assert r.json()[1]["id"] == org_id


def test_list_teams():
    r = requests.get(url=URL + "/teams/", timeout=2)
    assert r.status_code == 200
    assert r.json()[1]["id"] == team_id


def test_create_project():
    global project_id
    payload = {
        "name": f"test-{random.randint(1, 1000)}",
        "description": "Test API for Code Carbon",
        "team_id": team_id,
    }
    r = requests.put(url=URL + "/projects/", json=payload, timeout=2)
    print(r.json())
    assert r.status_code == 201
    assert r.json()["team_id"] == team_id
    project_id = r.json()["id"]


def test_create_experiment():
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
    r = requests.put(url=URL + "/experiment/", json=payload, timeout=2)
    print(r.json())
    assert r.status_code == 201
    assert r.json()["project_id"] == project_id
    experiment_id = r.json()["id"]


def test_create_run():
    global run_id
    payload = {"timestamp": "2021-04-04T08:43:00+02:00", "experiment_id": experiment_id}
    r = requests.put(url=URL + "/runs/", json=payload, timeout=2)
    print(r.json())
    assert r.status_code == 201
    run_id = r.json()["id"]


def test_create_emission():
    global run_id
    payload = {
        "timestamp": "2021-04-04T08:43:00+02:00",
        "run_id": run_id,
        "duration": random.randint(1, 100),
        "emissions": random.random() * random.randint(1, 10000),
        "energy_consumed": random.random() * random.randint(1, 10000),
    }
    print(payload)
    r = requests.put(url=URL + "/emissions/", json=payload, timeout=2)
    print(r.json())
    assert r.status_code == 201
