import dataclasses

import requests_mock

from codecarbon.core.api_client import ApiClient
from codecarbon.output import EmissionsData


def test_call_api():
    # mock_path = 'codecarbon.core.api_client.requests'
    with requests_mock.Mocker() as m:
        m.post(
            "http://test.com/run",
            json={"id": "82ba0923-0713-4da1-9e57-cea70b460ee9"},
            status_code=201,
        )
        api = ApiClient(
            experiment_id="experiment_id",
            endpoint_url="http://test.com",
            api_key="Toto",
        )
        assert api.run_id == "82ba0923-0713-4da1-9e57-cea70b460ee9"

    with requests_mock.Mocker() as m:
        m.post("http://test.com/emission", status_code=201)
        carbon_emission = EmissionsData(
            timestamp="222",
            project_name="",
            duration=1.5,
            emissions=2.0,
            energy_consumed=3.0,
            country_name="Groland",
            country_iso_code="GRD",
            region="EU",
            on_cloud="N",
            cloud_provider="",
            cloud_region="",
        )
        assert api.add_emission(dataclasses.asdict(carbon_emission))
