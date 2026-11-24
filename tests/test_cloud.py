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

import json

import requests
import responses
from responses import matchers

from codecarbon.core.cloud import CLOUD_METADATA_MAPPING, get_env_cloud_details


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


AWS_URL = CLOUD_METADATA_MAPPING["AWS"]["url"]
AWS_TOKEN_URL = "http://169.254.169.254/latest/api/token"


def setup_imdsv2_only_aws(metadata):
    """An EC2 instance that answers only requests carrying an IMDSv2 token."""

    def instance_identity(request):
        if request.headers.get("X-aws-ec2-metadata-token") == "a-token":
            return 200, {}, json.dumps(metadata)
        return 401, {}, ""

    responses.add_callback(responses.GET, AWS_URL, callback=instance_identity)
    for provider in ("Azure", "GCP"):
        responses.add(
            responses.GET, CLOUD_METADATA_MAPPING[provider]["url"], status=404
        )


@responses.activate
def test_get_env_cloud_details_aws_imdsv2_retries_with_a_token():
    metadata = {"architecture": "x86_64", "availabilityZone": "us-east-1a"}
    setup_imdsv2_only_aws(metadata)
    responses.add(
        responses.PUT,
        AWS_TOKEN_URL,
        body="a-token",
        match=[matchers.header_matcher({"X-aws-ec2-metadata-token-ttl-seconds": "60"})],
    )

    assert get_env_cloud_details() == {"provider": "AWS", "metadata": metadata}


@responses.activate
def test_get_env_cloud_details_aws_imdsv2_token_failure_is_not_aws():
    setup_imdsv2_only_aws({})
    responses.add(
        responses.PUT,
        AWS_TOKEN_URL,
        body=requests.exceptions.ConnectTimeout("hop limit reached"),
    )

    assert get_env_cloud_details() is None


@responses.activate
def test_get_env_cloud_details_aws_imdsv2_token_refused_is_not_aws():
    setup_imdsv2_only_aws({})
    responses.add(responses.PUT, AWS_TOKEN_URL, status=403)

    assert get_env_cloud_details() is None
