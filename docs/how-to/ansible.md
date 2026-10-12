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
├── host_vars
│   └── yourservername.yourdomain.com.yml
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

Update your CodeCarbon API credentials in `vars/main.yml`. These are shared by
every machine the playbook installs:

``` yaml
organization_id: your_org_id
project_id: your_project_id
api_key: your_api_key
```

### Step 3: Give Each Machine Its Own Experiment

An experiment identifies a single monitored machine on the dashboard. If several
servers report under the same `experiment_id`, their measurements are mixed into
one series and you can no longer tell them apart, so create one experiment per
machine on the dashboard.

Declare it in `host_vars/`, next to the `hosts` inventory. The file name must
match the host exactly as written in the inventory:

``` yaml
# host_vars/yourservername.yourdomain.com.yml
experiment_id: your_experiment_id_for_this_server
```

Add one such file per machine. Ansible loads it automatically, no change to the
playbook is needed:

``` text
host_vars
├── firstserver.yourdomain.com.yml
└── secondserver.yourdomain.com.yml
```

Do not put `experiment_id` back into `vars/main.yml`. That file is loaded with
`vars_files`, which takes precedence over `host_vars`, so a value left there
overrides every per-host file and silently sends all your machines to the same
experiment. The playbook stops with an explicit error if a host has no
`experiment_id` at all.

You can check what each host resolves to before deploying:

``` bash
ansible all -i hosts -m debug -a 'msg="{{ inventory_hostname }} -> {{ experiment_id }}"'
```

### Step 4: Run the Playbook

Execute the Ansible playbook to deploy CodeCarbon:

``` bash
ansible-playbook -i hosts tasks/main.yml
```

The playbook is idempotent, so you can run it again to add a machine or to
update the configuration of the existing ones. Changing the configuration
restarts the service, because CodeCarbon only reads `.codecarbon.config` at
startup.

## Next Steps

- [Install CodeCarbon as a Linux Service](linux-service.md) for manual setup details
- [Send emissions data to the cloud](cloud-api.md) to view results on the dashboard
- [Configure CodeCarbon](configuration.md) for additional customization
