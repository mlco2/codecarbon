from typing import Any, Dict, Optional

import requests

from codecarbon.external.logger import logger


def postprocess_gcp_cloud_metadata(cloud_metadata: Dict[str, Any]) -> Dict[str, Any]:
    # Attributes contains custom metadata and also contains Kubernetes config,
    # startup script and secrets, filter it out
    if "attributes" in cloud_metadata:
        del cloud_metadata["attributes"]

    return cloud_metadata


CLOUD_METADATA_MAPPING: Dict[str, Dict[str, Any]] = {
    "AWS": {
        "url": "http://169.254.169.254/latest/dynamic/instance-identity/document",
        "headers": {},
    },
    "Azure": {
        "url": "http://169.254.169.254/metadata/instance?api-version=2019-08-15",
        "headers": {"Metadata": "true"},
    },
    "GCP": {
        "url": "http://169.254.169.254/computeMetadata/v1/instance/?recursive=true&alt=json",  # noqa: E501
        "headers": {"Metadata-Flavor": "Google"},
        "postprocess_function": postprocess_gcp_cloud_metadata,
    },
}


def get_env_cloud_details(timeout: int = 1) -> Optional[Any]:
    """
    >>> get_env_cloud_details()
    {'provider': 'AWS',
     'metadata': {'accountId': '26550917306',
        'architecture': 'x86_64',
        'availabilityZone': 'us-east-1b',
        'billingProducts': None,
        'devpayProductCodes': None,
        'marketplaceProductCodes': None,
        'imageId': 'ami-025ed45832b817a35',
        'instanceId': 'i-7c3e81fed58d8f7f7',
        'instanceType': 'g4dn.2xlarge',
        'kernelId': None,
        'pendingTime': '2020-01-23T20:44:53Z',
        'privateIp': '172.156.72.143',
        'ramdiskId': None,
        'region': 'us-east-1',
        'version': '2017-09-30'}}
    """
    for provider in CLOUD_METADATA_MAPPING.keys():
        try:
            params = CLOUD_METADATA_MAPPING[provider]
            response = requests.get(
                params["url"], headers=params["headers"], timeout=timeout
            )
            response.raise_for_status()
            response_data = response.json()

            postprocess_function = params.get("postprocess_function")
            if postprocess_function is not None:
                response_data = postprocess_function(response_data)

            return {"provider": provider, "metadata": response_data}
        except requests.exceptions.RequestException:
            logger.debug("Not running on %s", provider)

    return None
