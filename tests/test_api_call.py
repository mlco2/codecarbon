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

    # ── Success-path tests (cover `return r.json()` after `r.raise_for_status()`) ──

    def test_check_auth_success(self):
        """Test check_auth returns JSON on 200."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            m.get(
                "http://test.com/auth/check",
                json={"user": "me"},
                status_code=200,
            )
            result = api.check_auth()
            self.assertEqual(result, {"user": "me"})

    def test_get_list_organizations_success(self):
        """Test get_list_organizations returns JSON on 200."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            orgs = [{"name": "Org1"}, {"name": "Org2"}]
            m.get(
                "http://test.com/organizations",
                json=orgs,
                status_code=200,
            )
            result = api.get_list_organizations()
            self.assertEqual(result, orgs)

    def test_get_organization_success(self):
        """Test get_organization returns JSON on 200."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            org = {"id": "org-1", "name": "TestOrg"}
            m.get(
                "http://test.com/organizations/org-1",
                json=org,
                status_code=200,
            )
            result = api.get_organization("org-1")
            self.assertEqual(result, org)

    def test_list_projects_from_organization_success(self):
        """Test list_projects_from_organization returns JSON on 200."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            projects = [{"id": "p1", "name": "Proj1"}]
            m.get(
                "http://test.com/organizations/org-1/projects",
                json=projects,
                status_code=200,
            )
            result = api.list_projects_from_organization("org-1")
            self.assertEqual(result, projects)

    def test_get_project_success(self):
        """Test get_project returns JSON on 200."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            project = {"id": "p1", "name": "TestProject"}
            m.get(
                "http://test.com/projects/p1",
                json=project,
                status_code=200,
            )
            result = api.get_project("p1")
            self.assertEqual(result, project)

    def test_list_experiments_from_project_success(self):
        """Test list_experiments_from_project returns JSON on 200."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            experiments = [{"id": "e1", "name": "Exp1"}]
            m.get(
                "http://test.com/projects/p1/experiments",
                json=experiments,
                status_code=200,
            )
            result = api.list_experiments_from_project("p1")
            self.assertEqual(result, experiments)

    def test_get_experiment_success(self):
        """Test get_experiment returns JSON on 200."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            exp = {"id": "e1", "name": "TestExperiment"}
            m.get(
                "http://test.com/experiments/e1",
                json=exp,
                status_code=200,
            )
            result = api.get_experiment("e1")
            self.assertEqual(result, exp)

    # ── Tests for methods with no coverage at all ──

    def test_check_organization_exists_found(self):
        """Test check_organization_exists returns org when found."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            orgs = [{"name": "MyOrg", "id": "org-1"}]
            m.get("http://test.com/organizations", json=orgs, status_code=200)
            result = api.check_organization_exists("MyOrg")
            self.assertEqual(result, {"name": "MyOrg", "id": "org-1"})

    def test_check_organization_exists_not_found(self):
        """Test check_organization_exists returns False when not found."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        with requests_mock.Mocker() as m:
            orgs = [{"name": "OtherOrg", "id": "org-2"}]
            m.get("http://test.com/organizations", json=orgs, status_code=200)
            result = api.check_organization_exists("MyOrg")
            self.assertFalse(result)

    def test_create_organization_success(self):
        """Test create_organization creates and returns JSON on 201."""
        from codecarbon.core.schemas import OrganizationCreate

        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        org = OrganizationCreate(name="NewOrg", description="A new org")
        with requests_mock.Mocker() as m:
            # check_organization_exists calls get_list_organizations
            m.get("http://test.com/organizations", json=[], status_code=200)
            m.post(
                "http://test.com/organizations",
                json={"id": "org-new", "name": "NewOrg", "description": "A new org"},
                status_code=201,
            )
            result = api.create_organization(org)
            self.assertEqual(result["name"], "NewOrg")

    def test_create_organization_already_exists(self):
        """Test create_organization returns existing org without POST."""
        from codecarbon.core.schemas import OrganizationCreate

        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        org = OrganizationCreate(name="ExistingOrg", description="Already there")
        with requests_mock.Mocker() as m:
            m.get(
                "http://test.com/organizations",
                json=[{"name": "ExistingOrg", "id": "org-existing"}],
                status_code=200,
            )
            result = api.create_organization(org)
            self.assertEqual(result["id"], "org-existing")

    def test_create_organization_error_raises(self):
        """Test create_organization raises HTTPError on server error."""
        from codecarbon.core.schemas import OrganizationCreate

        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        org = OrganizationCreate(name="NewOrg", description="A new org")
        with requests_mock.Mocker() as m:
            m.get("http://test.com/organizations", json=[], status_code=200)
            m.post("http://test.com/organizations", status_code=500)
            with self.assertRaises(requests.exceptions.HTTPError):
                api.create_organization(org)

    def test_update_organization_success(self):
        """Test update_organization returns JSON on 200."""
        from codecarbon.core.schemas import OrganizationCreate

        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        org = OrganizationCreate(name="Updated", description="Updated desc")
        org.id = "org-1"
        with requests_mock.Mocker() as m:
            m.patch(
                "http://test.com/organizations/org-1",
                json={"id": "org-1", "name": "Updated"},
                status_code=200,
            )
            result = api.update_organization(org)
            self.assertEqual(result["name"], "Updated")

    def test_update_organization_error_raises(self):
        """Test update_organization raises HTTPError on server error."""
        from codecarbon.core.schemas import OrganizationCreate

        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        org = OrganizationCreate(name="Updated", description="desc")
        org.id = "org-1"
        with requests_mock.Mocker() as m:
            m.patch("http://test.com/organizations/org-1", status_code=500)
            with self.assertRaises(requests.exceptions.HTTPError):
                api.update_organization(org)

    def test_create_project_success(self):
        """Test create_project returns JSON on 201."""
        from codecarbon.core.schemas import ProjectCreate

        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        project = ProjectCreate(
            name="NewProject", description="desc", organization_id="org-1"
        )
        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/projects",
                json={"id": "p1", "name": "NewProject"},
                status_code=201,
            )
            result = api.create_project(project)
            self.assertEqual(result["name"], "NewProject")

    def test_create_project_error_raises(self):
        """Test create_project raises HTTPError on server error."""
        from codecarbon.core.schemas import ProjectCreate

        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        project = ProjectCreate(
            name="NewProject", description="desc", organization_id="org-1"
        )
        with requests_mock.Mocker() as m:
            m.post("http://test.com/projects", status_code=500)
            with self.assertRaises(requests.exceptions.HTTPError):
                api.create_project(project)

    def test_add_experiment_success(self):
        """Test add_experiment returns JSON on 201."""
        from codecarbon.core.schemas import ExperimentCreate

        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        experiment = ExperimentCreate(
            timestamp="2021-04-04T08:43:00+02:00",
            name="TestExp",
            description="desc",
            on_cloud=False,
            project_id="00000000-0000-0000-0000-000000000001",
        )
        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/experiments",
                json={"id": "e1", "name": "TestExp"},
                status_code=201,
            )
            result = api.add_experiment(experiment)
            self.assertEqual(result["name"], "TestExp")

    def test_add_experiment_error_raises(self):
        """Test add_experiment raises HTTPError on server error."""
        from codecarbon.core.schemas import ExperimentCreate

        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=None,
            create_run_automatically=False,
        )
        experiment = ExperimentCreate(
            timestamp="2021-04-04T08:43:00+02:00",
            name="TestExp",
            description="desc",
            on_cloud=False,
            project_id="00000000-0000-0000-0000-000000000001",
        )
        with requests_mock.Mocker() as m:
            m.post("http://test.com/experiments", status_code=500)
            with self.assertRaises(requests.exceptions.HTTPError):
                api.add_experiment(experiment)

    def test_create_run_no_experiment_id_raises(self):
        """Test _create_run raises ValueError when experiment_id is None."""
        api = ApiClient(
            endpoint_url="http://test.com",
            api_key="Toto",
            conf=conf,
            create_run_automatically=False,
        )
        api.experiment_id = None
        with self.assertRaises(ValueError):
            api._create_run("some-experiment-id")
