# Deploy CodeCarbon CLI as a Service using Ansible

This section describes how to deploy CodeCarbon as a system service
using Ansible automation.

It automate the manual installation done in the previous chapter.

## What the Playbook Does

The Ansible playbook automates the following tasks:

-   Creates a dedicated system user and group for CodeCarbon
-   Sets up a Python virtual environment
-   Installs CodeCarbon package
-   Configures RAPL permissions for power measurements
-   Creates and configures the systemd service
-   Sets up the CodeCarbon configuration file
-   Starts and enables the service

## Prerequisites

-   Ansible installed on your machine
-   Debian-based target system(s)
-   SSH access to target system(s)
-   CodeCarbon API credentials from the dashboard

## Directory Structure

``` text
codecarbon/deploy/ansible/codecarbon_cli_as_a_service/
├── hosts
├── tasks
│   ├── install_codecarbon.yml
│   ├── main.yml
│   ├── rapl.yml
│   └── systemd_service.yml
├── templates
│   ├── codecarbon.config.j2
│   └── systemd_service.j2
└── vars
    └── main.yml
```

## Quick Start

### Step 1: Configure Target Hosts

Set the target server to install on in the `hosts` file:

``` text
yourservername.yourdomain.com   hostname=yourservername ansible_user=root ansible_ssh_private_key_file=~/.ssh/id_ed25519
```

### Step 2: Update Ansible Variables

Update your CodeCarbon API credentials in `vars/main.yml`:

``` yaml
organization_id: your_org_id
project_id: your_project_id
experiment_id: your_experiment_id
api_key: your_api_key
```

### Step 3: Run the Playbook

Execute the Ansible playbook to deploy CodeCarbon:

``` bash
ansible-playbook -i hosts tasks/main.yml
```

## Next Steps

- [Install CodeCarbon as a Linux Service](linux-service.md) for manual setup details
- [Send emissions data to the cloud](cloud-api.md) to view results on the dashboard
- [Configure CodeCarbon](configuration.md) for additional customization
