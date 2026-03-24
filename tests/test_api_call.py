import dataclasses
import unittest
from uuid import uuid4

import requests
import requests_mock

from codecarbon.core.api_client import ApiClient
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

    def test_create_run_error_raises(self):
        """Test that _create_run raises HTTPError on server error."""
        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/runs",
                status_code=500,
            )
            with self.assertRaises(requests.exceptions.HTTPError):
                ApiClient(
                    experiment_id="experiment_id",
                    endpoint_url="http://test.com",
                    api_key="Toto",
                    conf=conf,
                )

    def test_create_run_connection_error_raises(self):
        """Test that _create_run raises ConnectionError when API is unreachable."""
        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/runs",
                exc=requests.exceptions.ConnectionError("API unreachable"),
            )
            with self.assertRaises(requests.exceptions.ConnectionError):
                ApiClient(
                    experiment_id="experiment_id",
                    endpoint_url="http://test.com",
                    api_key="Toto",
                    conf=conf,
                )

    def test_add_emission_error_raises(self):
        """Test that add_emission raises HTTPError on server error."""
        with requests_mock.Mocker() as m:
            m.post("http://test.com/runs", json={"id": "run-id"}, status_code=201)
            api = ApiClient(
                experiment_id="experiment_id",
                endpoint_url="http://test.com",
                api_key="Toto",
                conf=conf,
            )
        with requests_mock.Mocker() as m:
            m.post("http://test.com/emissions", status_code=500)
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
            with self.assertRaises(requests.exceptions.HTTPError):
                api.add_emission(dataclasses.asdict(carbon_emission))

    def test_check_auth_error_raises(self):
        """Test that check_auth raises HTTPError on server error."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            m.get("http://test.com/auth/check", status_code=401)
            with self.assertRaises(requests.exceptions.HTTPError):
                api.check_auth()

    def test_get_list_organizations_error_raises(self):
        """Test that get_list_organizations raises HTTPError on server error."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            m.get("http://test.com/organizations", status_code=500)
            with self.assertRaises(requests.exceptions.HTTPError):
                api.get_list_organizations()

    def test_get_organization_error_raises(self):
        """Test that get_organization raises HTTPError on server error."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            m.get("http://test.com/organizations/org-id", status_code=500)
            with self.assertRaises(requests.exceptions.HTTPError):
                api.get_organization("org-id")

    def test_list_projects_error_raises(self):
        """Test that list_projects_from_organization raises HTTPError."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            m.get("http://test.com/organizations/org-id/projects", status_code=500)
            with self.assertRaises(requests.exceptions.HTTPError):
                api.list_projects_from_organization("org-id")

    def test_get_project_error_raises(self):
        """Test that get_project raises HTTPError on server error."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            m.get("http://test.com/projects/proj-id", status_code=500)
            with self.assertRaises(requests.exceptions.HTTPError):
                api.get_project("proj-id")

    def test_list_experiments_error_raises(self):
        """Test that list_experiments_from_project raises HTTPError."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            m.get("http://test.com/projects/proj-id/experiments", status_code=500)
            with self.assertRaises(requests.exceptions.HTTPError):
                api.list_experiments_from_project("proj-id")

    def test_get_experiment_error_raises(self):
        """Test that get_experiment raises HTTPError on server error."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            m.get("http://test.com/experiments/exp-id", status_code=500)
            with self.assertRaises(requests.exceptions.HTTPError):
                api.get_experiment("exp-id")
