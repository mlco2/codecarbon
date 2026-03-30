import dataclasses
import unittest
from uuid import uuid4

import requests_mock

from codecarbon.core.api_client import ApiClient
from codecarbon.core.schemas import ExperimentCreate, OrganizationCreate
from codecarbon.output import EmissionsData

conf = {
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
    "provider": "GCP",
    "ram_total_size": 83948.22,
    "tracking_mode": "Machine",
}


class TestApi(unittest.TestCase):
    def test_get_headers_prefers_api_key_over_access_token(self):
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="api-key",
            access_token="access-token",
            create_run_automatically=False,
        )

        headers = api._get_headers()

        self.assertEqual(headers["x-api-token"], "api-key")
        self.assertNotIn("Authorization", headers)

    def test_set_access_token_updates_client(self):
        api = ApiClient(endpoint_url="http://test.com", create_run_automatically=False)

        api.set_access_token("updated-token")

        self.assertEqual(api.access_token, "updated-token")

    def test_api_read_only(self):
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        self.assertIsNone(api.experiment_id)
        self.assertEqual(api.api_key, "Toto")
        self.assertEqual(api.url, "http://test.com")
        self.assertIsNone(api.run_id)

    def test_call_api(self):
        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/runs",
                json={
                    "id": "82ba0923-0713-4da1-9e57-cea70b460ee9",
                    "timestamp": "2021-04-04T08:43:00+02:00",
                    "experiment_id": "8edb03e1-9a28-452a-9c93-a3b6560136d7",
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
                    "ram_total_size": 83948.22,
                    "tracking_mode": "Machine",
                },
                status_code=201,
            )
            api = ApiClient(
                experiment_id="experiment_id",
                endpoint_url="http://test.com",
                api_key="Toto",
                conf=conf,
            )
            assert api.run_id == "82ba0923-0713-4da1-9e57-cea70b460ee9"

        with requests_mock.Mocker() as m:
            m.post("http://test.com/emissions", status_code=201)
            carbon_emission = EmissionsData(
                timestamp="222",
                project_name="",
                run_id=uuid4(),
                experiment_id="test",
                duration=1.5,
                emissions=2.0,
                emissions_rate=2.0,
                cpu_energy=2,
                gpu_energy=0,
                ram_energy=1,
                cpu_power=3.0,
                gpu_power=0,
                ram_power=0.15,
                energy_consumed=3.0,
                water_consumed=0.0,
                country_name="Groland",
                country_iso_code="GRD",
                region="EU",
                on_cloud="N",
                cloud_provider="",
                cloud_region="",
                os="Linux",
                python_version="3.8.0",
                codecarbon_version="2.1.3",
                gpu_count=4,
                gpu_model="NVIDIA",
                cpu_count=12,
                cpu_model="Intel",
                longitude=-7.6174,
                latitude=33.5822,
                ram_total_size=83948.22,
                tracking_mode="Machine",
            )
            assert api.add_emission(dataclasses.asdict(carbon_emission))

    def test_check_auth_returns_none_on_error(self):
        with requests_mock.Mocker() as m:
            m.get("http://test.com/auth/check", text="bad", status_code=401)
            api = ApiClient(
                endpoint_url="http://test.com",
                access_token="token",
                create_run_automatically=False,
            )

            self.assertIsNone(api.check_auth())

    def test_check_organization_exists_returns_false_when_list_fails(self):
        with requests_mock.Mocker() as m:
            m.get("http://test.com/organizations", text="bad", status_code=500)
            api = ApiClient(
                endpoint_url="http://test.com",
                create_run_automatically=False,
            )

            self.assertFalse(api.check_organization_exists("missing"))

    def test_create_organization_skips_when_name_exists(self):
        organization = OrganizationCreate(name="existing", description="desc")
        existing_org = {"id": "org-1", "name": "existing"}

        with requests_mock.Mocker() as m:
            m.get("http://test.com/organizations", json=[existing_org], status_code=200)
            api = ApiClient(
                endpoint_url="http://test.com",
                create_run_automatically=False,
            )

            self.assertEqual(api.create_organization(organization), existing_org)
            self.assertEqual(m.call_count, 1)

    def test_add_emission_returns_false_when_run_creation_fails(self):
        api = ApiClient(
            endpoint_url="http://test.com",
            experiment_id="exp-1",
            conf=conf,
            create_run_automatically=False,
        )

        api._create_run = lambda experiment_id: None

        self.assertFalse(
            api.add_emission(
                {
                    "duration": 2,
                    "emissions": 1.0,
                    "emissions_rate": 1.0,
                    "cpu_power": 1.0,
                    "gpu_power": 0.0,
                    "ram_power": 0.5,
                    "cpu_energy": 0.1,
                    "gpu_energy": 0.0,
                    "ram_energy": 0.1,
                    "energy_consumed": 0.2,
                }
            )
        )

    def test_add_emission_skips_short_duration(self):
        api = ApiClient(
            endpoint_url="http://test.com",
            experiment_id="exp-1",
            conf=conf,
            create_run_automatically=False,
        )
        api.run_id = "run-1"

        self.assertFalse(
            api.add_emission(
                {
                    "duration": 0.5,
                    "emissions": 1.0,
                    "emissions_rate": 1.0,
                    "cpu_power": 1.0,
                    "gpu_power": 0.0,
                    "ram_power": 0.5,
                    "cpu_energy": 0.1,
                    "gpu_energy": 0.0,
                    "ram_energy": 0.1,
                    "energy_consumed": 0.2,
                }
            )
        )

    def test_add_emission_returns_false_on_unsuccessful_post(self):
        with requests_mock.Mocker() as m:
            m.post("http://test.com/emissions", text="bad", status_code=500)
            api = ApiClient(
                endpoint_url="http://test.com",
                experiment_id="exp-1",
                conf=conf,
                create_run_automatically=False,
            )
            api.run_id = "run-1"

            self.assertFalse(
                api.add_emission(
                    {
                        "duration": 2,
                        "emissions": 1.0,
                        "emissions_rate": 1.0,
                        "cpu_power": 1.0,
                        "gpu_power": 0.0,
                        "ram_power": 0.5,
                        "cpu_energy": 0.1,
                        "gpu_energy": 0.0,
                        "ram_energy": 0.1,
                        "energy_consumed": 0.2,
                    }
                )
            )

    def test_create_run_returns_none_on_unsuccessful_status(self):
        with requests_mock.Mocker() as m:
            m.post("http://test.com/runs", text="bad", status_code=400)
            api = ApiClient(
                endpoint_url="http://test.com",
                experiment_id="experiment_id",
                api_key="Toto",
                conf=conf,
                create_run_automatically=False,
            )

            self.assertIsNone(api._create_run("experiment_id"))
            self.assertIsNone(api.run_id)

    def test_list_experiments_from_project_returns_empty_list_on_error(self):
        with requests_mock.Mocker() as m:
            m.get(
                "http://test.com/projects/proj-1/experiments",
                text="bad",
                status_code=500,
            )
            api = ApiClient(
                endpoint_url="http://test.com",
                create_run_automatically=False,
            )

            self.assertEqual(api.list_experiments_from_project("proj-1"), [])

    def test_set_experiment_updates_value(self):
        api = ApiClient(endpoint_url="http://test.com", create_run_automatically=False)

        api.set_experiment("exp-2")

        self.assertEqual(api.experiment_id, "exp-2")

    def test_add_experiment_returns_none_on_error(self):
        experiment = ExperimentCreate(
            timestamp="2024-01-01T00:00:00+00:00",
            name="exp",
            description="desc",
            on_cloud=False,
            project_id="proj-1",
        )
        with requests_mock.Mocker() as m:
            m.post("http://test.com/experiments", text="bad", status_code=500)
            api = ApiClient(
                endpoint_url="http://test.com",
                create_run_automatically=False,
            )

            self.assertIsNone(api.add_experiment(experiment))

    def test_get_experiment_returns_none_on_error(self):
        with requests_mock.Mocker() as m:
            m.get("http://test.com/experiments/exp-1", text="bad", status_code=404)
            api = ApiClient(
                endpoint_url="http://test.com",
                create_run_automatically=False,
            )

            self.assertIsNone(api.get_experiment("exp-1"))
