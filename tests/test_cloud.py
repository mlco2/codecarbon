# -*- coding: utf-8 -*-

# Copyright (C) 2020 [COMET-ML]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
# OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from unittest import mock

import responses

from codecarbon.core.cloud import CLOUD_METADATA_MAPPING, get_env_cloud_details
from codecarbon.emissions_tracker import EmissionsTracker


def setup_cloud_details_responses(tested_provider, provider_metadata):
    for provider, params in CLOUD_METADATA_MAPPING.items():
        if provider == tested_provider:
            responses.add(
                responses.GET, params["url"], json=provider_metadata, status=200
            )
        else:
            responses.add(responses.GET, params["url"], status=404)


@responses.activate
def test_get_env_cloud_details_mapping_aws():
    metadata = {"architecture": "x86_64", "availabilityZone": "us-east-1a"}
    setup_cloud_details_responses("AWS", metadata)

    assert get_env_cloud_details() == {"provider": "AWS", "metadata": metadata}


@responses.activate
def test_get_env_cloud_details_mapping_azure():
    metadata = {"compute": {"azEnvironment": "AzurePublicCloud"}}
    setup_cloud_details_responses("Azure", metadata)

    assert get_env_cloud_details() == {"provider": "Azure", "metadata": metadata}


@responses.activate
def test_get_env_cloud_details_mapping_google():
    metadata = {
        "attributes": {},
        "cpuPlatform": "Intel Haswell",
        "zone": "projects/253764845563/zones/us-central1-a",
    }
    setup_cloud_details_responses("GCP", metadata)

    expected_metadata = metadata
    del expected_metadata["attributes"]

    assert get_env_cloud_details() == {"provider": "GCP", "metadata": metadata}


@responses.activate
def test_get_env_cloud_details_mapping_google_empty_payload():
    metadata = {}
    setup_cloud_details_responses("GCP", metadata)

    assert get_env_cloud_details() == {"provider": "GCP", "metadata": metadata}


@responses.activate
def test_get_env_cloud_details_mapping_nothing():
    metadata = {"instance": {"attributes": {"cluster-location": "us-east1-c"}}}
    setup_cloud_details_responses("localhost", metadata)

    assert get_env_cloud_details() is None


def test_cloud_detection_disabled_makes_no_request():
    with mock.patch(
        "codecarbon.external.geography.get_env_cloud_details"
    ) as mocked_get_env_cloud_details:
        tracker = EmissionsTracker(cloud_detection=False, allow_multiple_runs=True)
        cloud = tracker._get_cloud_metadata()

    mocked_get_env_cloud_details.assert_not_called()
    assert cloud.is_on_private_infra
