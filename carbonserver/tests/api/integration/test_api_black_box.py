"""
To test it, you need to set:
export CODECARBON_API_URL=http://localhost:8008
export DATABASE_URL=postgresql://codecarbon-user:supersecret@localhost:5480/codecarbon_db
Then execute the tests:
hatch run api:test-integ
"""

import os
import unittest
import uuid
from datetime import datetime

import pytest
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from carbonserver.config import settings

tc = unittest.TestCase()

# Get the API url to use from an env variable if exist
URL = os.getenv("CODECARBON_API_URL")
if URL is None:
    pytest.exit("CODECARBON_API_URL is not defined")


experiment_id = project_id = user_id = api_key = org_id = None
org_name = org_description = org_new_id = None
project_token_id = PROJECT_TOKEN = None
emission_id = None
USER_PASSWORD = "Secret1!îstring"
USER_EMAIL = "user@integration.test"
MISSING_UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def get_datetime():
    t = datetime.timestamp(datetime.now())
    return str(datetime.fromtimestamp(t).isoformat())


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


# def test_api01_user_create():
#     tc.assertIsNotNone(URL)
#     # we delete it if exist
#     del_test_user()
#     payload = {
#         "email": USER_EMAIL,
#         "name": "toto",
#         "password": USER_PASSWORD,
#     }
#     r = requests.post(url=URL + "/user", json=payload, timeout=2)
#     tc.assertEqual(r.status_code, 201)
#     tc.assertEqual(r.json()["email"], USER_EMAIL)
#     tc.assertTrue(r.json()["is_active"])


# def test_api02_user_signup():
#     global user_id, org_id, team_id, api_key
#     # signup is creating a user, we delete it if exist
#     del_test_user()
#     payload = {
#         "email": USER_EMAIL,
#         "name": "toto",
#         "password": USER_PASSWORD,
#     }
#     r = requests.post(url=URL + "/user/signup/", json=payload, timeout=2)
#     tc.assertEqual(r.status_code, 201)
#     tc.assertEqual(r.json()["email"], USER_EMAIL)
#     tc.assertTrue(r.json()["is_active"])
#     user_id = r.json()["id"]
#     api_key = r.json()["api_key"]
#     org_id = r.json()["organizations"][0]
#     team_id = r.json()["teams"][0]


# def test_api03_users_list():
#     r = requests.get(url=URL + "/users", timeout=2)
#     tc.assertEqual(r.status_code, 200)
#     assert is_key_value_exist(r.json(), "id", user_id)


# def test_api04_get_user():
#     r = requests.get(url=URL + "/user/" + user_id, timeout=2)
#     tc.assertEqual(r.status_code, 200)
#     assert r.json()["id"] == user_id
#     tc.assertEqual(r.json()["email"], USER_EMAIL)


# def test_api05_auth_success():
#     payload = {"email": USER_EMAIL, "password": USER_PASSWORD}
#     r = requests.post(url=URL + "/authenticate/", json=payload, timeout=2)
#     tc.assertEqual(r.status_code, 200)
#     assert r.json()["access_token"] == "a"
#     assert r.json()["token_type"] == "access"


# def test_api06_auth_wrong_email():
#     payload = {
#         "email": "long.user.email.that.cant.exist.3495739@asdfijvneurvbier.fr",
#         "password": USER_PASSWORD,
#     }
#     r = requests.post(url=URL + "/authenticate/", json=payload, timeout=2)
#     assert r.status_code == 401


# def test_api07_auth_wrong_password():
#     payload = {"email": USER_EMAIL, "password": "wrong-password"}
#     r = requests.post(url=URL + "/authenticate/", json=payload, timeout=2)
#     assert r.status_code == 401


# def test_api08_user_deleted():
#     del_test_user()
#     payload = {"email": USER_EMAIL, "password": USER_PASSWORD}
#     r = requests.post(url=URL + "/authenticate/", json=payload, timeout=2)
#     assert r.status_code == 401


def test_api00_uuid_missing():
    for route in ["organization", "project", "experiment", "emission", "run"]:
        r = requests.get(url=URL + f"/{route}/" + MISSING_UUID, timeout=2)
        tc.assertEqual(
            r.status_code, 404, msg=f"{r.status_code}!=404 for {route} : {r.content}"
        )


def test_api09_organization_create():
    global org_new_id, org_name, org_description
    org_name = "test_to_delete"
    org_description = "test to delete"
    payload = {"name": org_name, "description": org_description}
    r = requests.post(url=URL + "/organizations", json=payload, timeout=2)
    tc.assertEqual(r.status_code, 201)
    assert r.json()["name"] == org_name
    assert r.json()["description"] == org_description
    org_new_id = r.json()["id"]


def test_api10_organization_read():
    r = requests.get(url=URL + "/organizations/" + org_new_id, timeout=2)
    tc.assertEqual(r.status_code, 200)
    assert r.json()["name"] == org_name
    assert r.json()["description"] == org_description


def test_api11_organization_list():
    r = requests.get(url=URL + "/organizations", timeout=2)
    tc.assertEqual(r.status_code, 200)
    assert r.json()[-1]["id"] == org_new_id


def test_api16_project_create():
    global project_id
    payload = {
        "name": "test_to_delete",
        "description": "Test to delete by test_api_black_box",
        "organization_id": org_new_id,
    }
    r = requests.post(url=URL + "/projects/", json=payload, timeout=2)
    tc.assertEqual(r.status_code, 201)
    project_id = r.json()["id"]


def test_api16_project_lastrun_empty():
    """
    Test that empty result works.
    """
    url = f"{URL}/lastrun/project/{project_id}/"
    r = requests.get(url, timeout=2)
    tc.assertEqual(r.status_code, 200)
    assert len(r.json()) == 0


def test_api18_experiment_create():
    global experiment_id
    payload = {
        "name": "test_api_black_box",
        "description": "Created by test_api_black_box",
        "timestamp": get_datetime(),
        "country_name": "France",
        "country_iso_code": "FRA",
        "region": "france",
        "on_cloud": True,
        "cloud_provider": "Premise",
        "cloud_region": "eu-west-1a",
        "project_id": project_id,
    }
    r = requests.post(url=URL + "/experiments", json=payload, timeout=2)
    tc.assertEqual(r.status_code, 201)
    tc.assertEqual(r.json()["project_id"], project_id)
    experiment_id = r.json()["id"]
    tc.assertTrue(is_valid_uuid(experiment_id))


def test_api19_experiment_read():
    r = requests.get(url=URL + "/experiments/" + experiment_id, timeout=2)
    tc.assertEqual(r.status_code, 200)
    assert r.json()["id"] == experiment_id


def test_api20_experiment_list():
    r = requests.get(url=f"{URL}/projects/{project_id}/experiments", timeout=2)
    tc.assertEqual(r.status_code, 200)
    assert is_key_value_exist(r.json(), "id", experiment_id)


def test_api21_create_api_project_token():
    # This project token is needed to create emissions/runs
    global PROJECT_TOKEN
    global project_token_id
    assert project_id is not None
    payload = {
        "name": "Project token for test_api_black_box",
        "access": 2,
    }
    r = requests.post(
        url=URL + f"/projects/{project_id}/api-tokens", json=payload, timeout=2
    )
    tc.assertEqual(r.status_code, 201)
    PROJECT_TOKEN = r.json()["token"]
    project_token_id = r.json()["id"]


def send_run(experiment_id: str):
    assert experiment_id is not None
    payload = {
        "timestamp": get_datetime(),
        "experiment_id": experiment_id,
        "os": "macOS-10.15.7-x86_64-i386-64bit",
        "python_version": "3.8.0",
        "codecarbon_version": "2.1.3",
        "cpu_count": 12,
        "cpu_model": "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz",
        "gpu_count": 4,
        "gpu_model": "NVIDIA",
        "longitude": -7.6174,
        "latitude": 33.5822,
        "region": "EUROPE",
        "provider": "AWS",
        "ram_total_size": 16948.22,
        "tracking_mode": "Machine",
    }
    r = requests.post(
        url=URL + "/runs/",
        json=payload,
        timeout=2,
        headers={"x-api-token": PROJECT_TOKEN},
    )
    tc.assertEqual(r.status_code, 201)
    return r.json()


def test_api21_run_create():
    global run_id
    resp = send_run(experiment_id)
    run_id = resp["id"]


def test_api21_run_create2():
    global run_id_2
    resp = send_run(experiment_id)
    run_id_2 = resp["id"]


def test_api22_run_read():
    r = requests.get(url=URL + "/runs/" + run_id, timeout=2)
    tc.assertEqual(r.status_code, 200)
    tc.assertEqual(r.json()["id"], run_id)
    tc.assertEqual(r.json()["codecarbon_version"], "2.1.3")


def test_api23_run_list():
    r = requests.get(url=URL + "/runs", timeout=2)
    tc.assertEqual(r.status_code, 200)
    tc.assertTrue(is_key_value_exist(r.json(), "id", run_id))
    tc.assertTrue(is_key_value_exist(r.json(), "id", run_id_2))


def test_api24_runs_for_experiment_list():
    r = requests.get(url=f"{URL}/experiments/{experiment_id}/runs", timeout=2)
    tc.assertEqual(r.status_code, 200)
    assert is_key_value_exist(r.json(), "id", run_id)
    assert is_key_all_values_equal(r.json(), "experiment_id", experiment_id)


default_emission = {
    "duration": 10,
    "emissions_sum": 100.50,
    "emissions_rate": 10.50,
    "cpu_power": 0.5,
    "gpu_power": 200.50,
    "ram_power": 1.50,
    "cpu_energy": 50.50,
    "gpu_energy": 105.50,
    "ram_energy": 60.50,
    "energy_consumed": 65.50,
}


def add_emission(run_id: str):
    tc.assertIsNotNone(run_id)
    payload = {
        "timestamp": get_datetime(),
        "run_id": run_id,
        "duration": default_emission["duration"],
        "emissions_sum": default_emission["emissions_sum"],
        "emissions_rate": default_emission["emissions_rate"],
        "cpu_power": default_emission["cpu_power"],
        "gpu_power": default_emission["gpu_power"],
        "ram_power": default_emission["ram_power"],
        "cpu_energy": default_emission["cpu_energy"],
        "gpu_energy": default_emission["gpu_energy"],
        "ram_energy": default_emission["ram_energy"],
        "energy_consumed": default_emission["energy_consumed"],
    }
    r = requests.post(
        url=URL + "/emissions/",
        json=payload,
        timeout=2,
        headers={"x-api-token": PROJECT_TOKEN},
    )
    tc.assertEqual(r.status_code, 201)
    return r.json()


def test_api25_emission_create():
    r = add_emission(run_id)
    tc.assertTrue(is_valid_uuid(r))
    r = add_emission(run_id)
    tc.assertTrue(is_valid_uuid(r))
    r = add_emission(run_id_2)
    tc.assertTrue(is_valid_uuid(r))
    r = add_emission(run_id_2)
    tc.assertTrue(is_valid_uuid(r))


def test_api26_emission_list():
    global emission_id
    r = requests.get(url=f"{URL}/runs/{run_id}/emissions", timeout=2)
    tc.assertEqual(r.status_code, 200)
    assert is_key_all_values_equal(r.json()["items"], "run_id", run_id)
    emission_id = r.json()["items"][-1]["id"]


def test_api27_emission_read():
    r = requests.get(url=URL + "/emissions/" + emission_id, timeout=2)
    tc.assertEqual(r.status_code, 200)
    r = r.json()
    assert r["id"] == emission_id
    assert r["run_id"] == run_id
    for k, v in default_emission.items():
        tc.assertEqual(r[k], v)


def test_api27_read_all():
    # Check the organization
    r = requests.get(url=URL + "/organizations/" + org_new_id, timeout=2)
    assert r.json()["name"] == org_name
    # Check the experiment
    r = requests.get(url=f"{URL}/projects/{project_id}/experiments", timeout=2)
    assert is_key_value_exist(r.json(), "id", experiment_id)
    # Check the run
    r = requests.get(url=f"{URL}/experiments/{experiment_id}/runs", timeout=2)
    assert is_key_value_exist(r.json(), "id", run_id)
    # Check the emission
    r = requests.get(url=f"{URL}/runs/{run_id}/emissions", timeout=2)
    assert is_key_all_values_equal(r.json()["items"], "run_id", run_id)
    emission_id = r.json()["items"][-1]["id"]
    tc.assertTrue(is_valid_uuid(emission_id))


def test_api29_experiment_read_detailed_sums():
    url = f"{URL}/projects/{project_id}/experiments/sums/"
    r = requests.get(url, timeout=2)
    tc.assertEqual(r.status_code, 200)
    r = r.json()

    assert len(r) > 0
    assert r[0]["experiment_id"] == experiment_id
    # assert r[0]["duration"] == 98745.0
    for experiment_sum in r:
        tc.assertEqual(experiment_sum["emissions_count"], 4)
        tc.assertEqual(
            experiment_sum["emissions"], default_emission["emissions_sum"] * 4
        )
        for k, v in default_emission.items():
            """{'experiment_id': 'db1ba567-3bd2-4ad0-8024-e4fa71f8a203', 'timestamp': '2022-04-23T23:04:43.634455', 'name': 'test_api_black_box',
            'description': 'Created by test_api_black_box', 'country_name': 'France', 'country_iso_code': 'FRA', 'region': 'france', 'on_cloud': True,
             'cloud_provider': 'Premise', 'cloud_region': 'eu-west-1a', 'emissions': 402.0, 'cpu_power': 0.5, 'gpu_power': 200.5, 'ram_power': 1.5,
              'cpu_energy': 202.0, 'gpu_energy': 422.0, 'ram_energy': 242.0, 'energy_consumed': 262.0, 'duration': 40.0, 'emissions_rate': 10.5,
               'emissions_count': 4}
            """

            if k in [
                "emissions",
                "cpu_energy",
                "gpu_energy",
                "ram_energy",
                "energy_consumed",
                "duration",
            ]:
                tc.assertEqual(
                    experiment_sum[k], v * 4, f"{k}:{v} vs emission={experiment_sum}"
                )
            if k in ["cpu_power", "gpu_power", "ram_power", "emissions_rate"]:
                tc.assertEqual(
                    experiment_sum[k], v, f"{k}:{v} vs emission={experiment_sum}"
                )


# TODO: Do assert on all results
def test_api30_run_read_detailed_sums():
    url = f"{URL}/experiments/{experiment_id}/runs/sums"
    r = requests.get(url, timeout=2)
    tc.assertEqual(r.status_code, 200, msg=f"{url=} {r.content=}")
    """
    [
        {'run_id': '1e614f0c-f1cb-4ce3-9183-d0df8e28566d', 'timestamp': '2022-04-23T23:11:05.377152', 'emissions': 201.0, 'cpu_power': 0.5,
         'gpu_power': 200.5, 'ram_power': 1.5, 'cpu_energy': 101.0, 'gpu_energy': 211.0, 'ram_energy': 121.0, 'energy_consumed': 131.0,
          'duration': 20.0, 'emissions_rate': 10.5, 'emissions_count': 2},
        {'run_id': '3bd34980-631e-4703-8388-c4dd630b0e8c', 'timestamp': '2022-04-23T23:11:05.400162', 'emissions': 201.0, 'cpu_power': 0.5,
         'gpu_power': 200.5, 'ram_power': 1.5, 'cpu_energy': 101.0, 'gpu_energy': 211.0, 'ram_energy': 121.0, 'energy_consumed': 131.0,
         'duration': 20.0, 'emissions_rate': 10.5, 'emissions_count': 2}
    ]
    """
    r = r.json()
    assert len(r) > 0
    assert r[0]["run_id"] in [run_id, run_id_2]
    for run_sum in r:
        tc.assertEqual(run_sum["emissions_count"], 2)
        tc.assertEqual(run_sum["emissions"], default_emission["emissions_sum"] * 2)
        for k, v in default_emission.items():
            if k in [
                "emissions",
                "cpu_energy",
                "gpu_energy",
                "ram_energy",
                "energy_consumed",
                "duration",
            ]:
                tc.assertEqual(run_sum[k], v * 2, f"{k}:{v} vs emission={run_sum}")
            if k in ["cpu_power", "gpu_power", "ram_power", "emissions_rate"]:
                tc.assertEqual(run_sum[k], v, f"{k}:{v} vs emission={run_sum}")


def test_api31_project_read_detailed_sums():
    url = f"{URL}/projects/{project_id}/sums/"
    r = requests.get(url, timeout=2)
    tc.assertEqual(r.status_code, 200, msg=f"{url=} {r.content=}")
    r = r.json()
    assert len(r) > 0
    assert r["project_id"] == project_id
    project_sum = r
    expected_count = 4
    tc.assertEqual(project_sum["emissions_count"], expected_count)
    tc.assertEqual(
        project_sum["emissions"], default_emission["emissions_sum"] * expected_count
    )
    for k, v in default_emission.items():
        if k in [
            "emissions",
            "cpu_energy",
            "gpu_energy",
            "ram_energy",
            "energy_consumed",
            "duration",
        ]:
            tc.assertEqual(
                project_sum[k], v * expected_count, f"{k}:{v} vs emission={project_sum}"
            )
        if k in ["cpu_power", "gpu_power", "ram_power", "emissions_rate"]:
            tc.assertEqual(project_sum[k], v, f"{k}:{v} vs emission={project_sum}")


def test_api32_organization_read_detailed_sums():
    url = f"{URL}/organizations/{org_new_id}/sums/"
    r = requests.get(url, timeout=2)
    tc.assertEqual(r.status_code, 200, msg=f"{url=} {r.content=}")
    assert len(r.json()) > 0
    assert r.json()["organization_id"] == org_new_id
    organization_sum = r.json()
    expected_count = 4
    tc.assertEqual(organization_sum["emissions_count"], expected_count)
    tc.assertEqual(
        organization_sum["emissions"],
        default_emission["emissions_sum"] * expected_count,
    )
    for k, v in default_emission.items():
        if k in [
            "emissions",
            "cpu_energy",
            "gpu_energy",
            "ram_energy",
            "energy_consumed",
            "duration",
        ]:
            tc.assertEqual(
                organization_sum[k],
                v * expected_count,
                f"{k}:{v} vs emission={organization_sum}",
            )
        if k in ["cpu_power", "gpu_power", "ram_power", "emissions_rate"]:
            tc.assertEqual(
                organization_sum[k], v, f"{k}:{v} vs emission={organization_sum}"
            )


def test_api33_project_read_last_run():
    url = f"{URL}/lastrun/project/{project_id}/"
    r = requests.get(url, timeout=2)
    tc.assertEqual(r.status_code, 200)
    assert len(r.json()) > 0
    assert r.json()["id"] == run_id_2
    assert r.json()["experiment_id"] == experiment_id


def test_api34_project_api_token_delete():
    url = f"{URL}/projects/{project_id}/api-tokens/{project_token_id}"
    r = requests.delete(url, timeout=2)
    tc.assertEqual(r.status_code, 204)
