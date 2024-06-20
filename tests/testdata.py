import pynvml as real_pynvml

GEO_METADATA_USA = {
    "organization_name": "foobar",
    "region": "Illinois",
    "accuracy": 1,
    "asn": 0,
    "organization": "foobar",
    "timezone": "America/Chicago",
    "longitude": "88",
    "country_code3": "USA",
    "area_code": "0",
    "ip": "foobar",
    "city": "Chicago",
    "country": "United States",
    "continent_code": "NA",
    "country_code": "US",
    "latitude": "0",
}

GEO_METADATA_USA_BACKUP = {
    "organization_name": "foobar",
    "regionName": "Illinois",
    "accuracy": 1,
    "asn": 0,
    "organization": "foobar",
    "timezone": "America/Chicago",
    "lon": "88",
    "area_code": "0",
    "ip": "foobar",
    "city": "Chicago",
    "country": "United States",
    "countryCode": "US",
    "lat": "0",
}

COUNTRY_METADATA_USA = {
    "status": "OK",
    "status-code": 200,
    "version": "1.0",
    "access": "public",
    "data": {
        "USA": {
            "id": "USA",
            "country": "United States of America (the)",
            "region": "North America",
        },
        "UMI": {
            "id": "UMI",
            "country": "United States Minor Outlying Islands (the)",
            "region": "Oceania",
        },
    },
}

GEO_METADATA_CANADA = {
    "organization_name": "foobar",
    "region": "Ontario",
    "accuracy": 100,
    "asn": 0,
    "organization": "foobar",
    "timezone": "America/Toronto",
    "longitude": "1",
    "country_code3": "CAN",
    "area_code": "0",
    "ip": "foobar",
    "city": "Toronto",
    "country": "Canada",
    "continent_code": "NA",
    "country_code": "CA",
    "latitude": "1",
}

CLOUD_METADATA_AWS = {
    "provider": "AWS",
    "metadata": {
        "accountId": "26550917306",
        "architecture": "x86_64",
        "availabilityZone": "us-east-1b",
        "billingProducts": None,
        "devpayProductCodes": None,
        "marketplaceProductCodes": None,
        "imageId": "ami-025ed45832b817a35",
        "instanceId": "i-7c3e81fed58d8f7f7",
        "instanceType": "g4dn.2xlarge",
        "kernelId": None,
        "pendingTime": "2020-01-23T20:44:53Z",
        "privateIp": "172.156.72.143",
        "ramdiskId": None,
        "region": "us-east-1",
        "version": "2017-09-30",
    },
}

CLOUD_METADATA_AZURE = {
    "experimentKey": "763fa7716ed2438997223413e397f31e",
    "metadata": {
        "compute": {
            "azEnvironment": "AzurePublicCloud",
            "customData": "",
            "location": "eastus",
            "name": "comet-repository",
            "offer": "UbuntuServer",
            "osType": "Linux",
            "placementGroupId": "",
            "plan": {"name": "", "product": "", "publisher": ""},
            "platformFaultDomain": "0",
            "platformUpdateDomain": "0",
            "provider": "Microsoft.Compute",
            "publisher": "Canonical",
            "resourceGroupName": "comet",
            "sku": "18.04-LTS",
            "subscriptionId": "66bc3084-fa17-4852-a9c8-4c449bd8514d",
            "tags": "",
            "tagsList": [],
            "version": "18.04.201904020",
            "vmId": "4fbdfa71-3564-48d3-851c-df54e6ba44ca",
            "vmScaleSetName": "",
            "vmSize": "Standard_D2s_v3",
            "zone": "",
        },
        "network": {
            "interface": [
                {
                    "ipv4": {
                        "ipAddress": [
                            {
                                "privateIpAddress": "10.0.0.23",
                                "publicIpAddress": "104.211.33.237",
                            }
                        ],
                        "subnet": [{"address": "10.0.0.0", "prefix": "24"}],
                    },
                    "ipv6": {"ipAddress": []},
                    "macAddress": "000D3A1FEDC1",
                }
            ]
        },
    },
    "provider": "Azure",
}


CLOUD_METADATA_GCP = {
    "experimentKey": "3e84c36ba22c449a9eefdc077f640d30",
    "metadata": {
        "cpuPlatform": "Intel Haswell",
        "description": "",
        "disks": [
            {
                "deviceName": "instance-2",
                "index": 0,
                "mode": "READ_WRITE",
                "type": "PERSISTENT",
            }
        ],
        "guestAttributes": {},
        "hostname": "instance-2.c.onprem-test-214916.internal",
        "id": 1794043451263962812,
        "image": "projects/debian-cloud/global/images/debian-9-stretch-v20200309",
        "legacyEndpointAccess": {"0.1": 0, "v1beta1": 0},
        "licenses": [{"id": "1000205"}],
        "machineType": "projects/705208488469/machineTypes/f1-micro",
        "maintenanceEvent": "NONE",
        "name": "instance-2",
        "networkInterfaces": [
            {
                "accessConfigs": [
                    {"externalIp": "34.71.112.18", "type": "ONE_TO_ONE_NAT"}
                ],
                "dnsServers": ["169.254.169.254"],
                "forwardedIps": [],
                "gateway": "10.128.0.1",
                "ip": "10.128.0.7",
                "ipAliases": [],
                "mac": "42:01:0a:80:00:07",
                "mtu": 1460,
                "network": "projects/705208488469/networks/default",
                "subnetmask": "255.255.240.0",
                "targetInstanceIps": [],
            }
        ],
        "preempted": "FALSE",
        "remainingCpuTime": -1,
        "scheduling": {
            "automaticRestart": "TRUE",
            "onHostMaintenance": "MIGRATE",
            "preemptible": "FALSE",
        },
        "serviceAccounts": {
            "705208488469-compute@developer.gserviceaccount.com": {
                "aliases": ["default"],
                "email": "705208488469-compute@developer.gserviceaccount.com",
                "scopes": [
                    "https://www.googleapis.com/auth/devstorage.read_only",
                    "https://www.googleapis.com/auth/logging.write",
                    "https://www.googleapis.com/auth/monitoring.write",
                    "https://www.googleapis.com/auth/servicecontrol",
                    "https://www.googleapis.com/auth/service.management.readonly",
                    "https://www.googleapis.com/auth/trace.append",
                ],
            },
            "default": {
                "aliases": ["default"],
                "email": "705208488469-compute@developer.gserviceaccount.com",
                "scopes": [
                    "https://www.googleapis.com/auth/devstorage.read_only",
                    "https://www.googleapis.com/auth/logging.write",
                    "https://www.googleapis.com/auth/monitoring.write",
                    "https://www.googleapis.com/auth/servicecontrol",
                    "https://www.googleapis.com/auth/service.management.readonly",
                    "https://www.googleapis.com/auth/trace.append",
                ],
            },
        },
        "tags": [],
        "virtualClock": {"driftToken": "0"},
        "zone": "projects/705208488469/zones/us-central1-a",
    },
    "provider": "GCP",
}

CLOUD_METADATA_GCP_EMPTY = {
    "experimentKey": "3e84c36ba22c449a9eefdc077f640d30",
    "metadata": {},
    "provider": "GCP",
}

SINGLE_GPU_DETAILS_RESPONSE = [
    {
        "name": "Tesla V100-SXM2-16GB",
        "uuid": "GPU-4e817856-1fb8-192a-7ab7-0e0e4476c184",
        "free_memory": 16945381376,
        "total_memory": 16945512448,
        "used_memory": 131072,
        "temperature": 28,
        "power_usage": 42159,
        "power_limit": 300000,
        "total_energy_consumption": 149709,
        "gpu_utilization": 0,
        "compute_mode": 0,
        "compute_processes": [],
        "graphics_processes": [],
    }
]

TWO_GPU_DETAILS_RESPONSE = [
    {
        "name": "Tesla V100-SXM2-16GB",
        "uuid": "foo",
        "free_memory": 16945381376,
        "total_memory": 16945512448,
        "used_memory": 131072,
        "temperature": 28,
        "power_usage": 42159,
        "power_limit": 300000,
        "total_energy_consumption": 149709,
        "gpu_utilization": 0,
        "compute_mode": 0,
        "compute_processes": [],
        "graphics_processes": [],
    },
    {
        "name": "Tesla V100-SXM2-16GB",
        "uuid": "bar",
        "free_memory": 16945381376,
        "total_memory": 16945512448,
        "used_memory": 131072,
        "temperature": 28,
        "power_usage": 32159,
        "power_limit": 300000,
        "total_energy_consumption": 149709,
        "gpu_utilization": 0,
        "compute_mode": 0,
        "compute_processes": [],
        "graphics_processes": [],
    },
]

TWO_GPU_DETAILS_RESPONSE_HANDLES = {
    "handle_0": {
        "name": "Tesla V100-SXM2-16GB",
        "uuid": "foo",
        "memory": real_pynvml.c_nvmlMemory_t(1024, 200, 824),
        "temperature": 28,
        "power_usage": 42159,
        "power_limit": 300000,
        "total_energy_consumption": 149709,
        "gpu_utilization": 0,
        "compute_mode": 0,
        "compute_processes": [],
        "graphics_processes": [],
    },
    "handle_1": {
        "name": "Tesla V100-SXM2-16GB",
        "uuid": "bar",
        "memory": real_pynvml.c_nvmlMemory_t(1024, 200, 824),
        "temperature": 28,
        "power_usage": 32159,
        "power_limit": 300000,
        "total_energy_consumption": 149709,
        "gpu_utilization": 0,
        "compute_mode": 0,
        "compute_processes": [],
        "graphics_processes": [],
    },
}
