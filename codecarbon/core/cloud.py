from concurrent.futures import ThreadPoolExecutor
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

    All providers are probed at once. Off cloud that is one timeout instead of
    one per provider; on a cloud it is slower than returning on the first hit,
    because the pool is only left once every probe has finished.
    """
    providers = list(CLOUD_METADATA_MAPPING.keys())

    # Off cloud every provider times out, and sequentially that is one timeout each.
    with ThreadPoolExecutor(max_workers=len(providers)) as executor:
        futures = [executor.submit(_probe_provider, p, timeout) for p in providers]
        # Resolve in mapping order, not completion order, so detection stays
        # deterministic if more than one provider answers.
        for provider, future in zip(providers, futures):
            response_data = future.result()
            if response_data is not None:
                return {"provider": provider, "metadata": response_data}

    return None


def _probe_provider(provider: str, timeout: int) -> Optional[Dict[str, Any]]:
    params = CLOUD_METADATA_MAPPING[provider]
    try:
        response = requests.get(
            params["url"], headers=params["headers"], timeout=timeout
        )
        response.raise_for_status()
        response_data = response.json()
    except requests.exceptions.RequestException:
        logger.debug("Not running on %s", provider)
        return None

    postprocess_function = params.get("postprocess_function")
    if postprocess_function is not None:
        response_data = postprocess_function(response_data)

    return response_data
