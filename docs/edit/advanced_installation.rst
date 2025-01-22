Advanced Installation
=====================

Install CodeCarbon as a Linux service
`````````````````````````````````````

To install CodeCarbon as a Linux service, follow the instructions below. It works on Ubuntu or other Debian-based systems using systemd.

Create a dedicated user:

.. code-block::  bash

    sudo useradd -r -s /bin/false codecarbon

Create a directory for the CodeCarbon service:

.. code-block::  bash

    sudo mkdir /opt/codecarbon

Change the ownership of the directory to the user created above:

.. code-block::  bash

    sudo chown codecarbon:codecarbon /opt/codecarbon

Create a virtual environment for CodeCarbon :

.. code-block::  bash

    sudo apt install python3-venv
    sudo -u codecarbon python3 -m venv /opt/codecarbon/.venv

Install CodeCarbon in the virtual environment:

.. code-block::  bash

    sudo -u codecarbon /opt/codecarbon/.venv/bin/pip install codecarbon

Go to https://dashboard.codecarbon.io/ and create an account to get your API key.

Configure CodeCarbon:

.. code-block::  bash

    sudo -u codecarbon /opt/codecarbon/.venv/bin/codecarbon login

Create a systemd service file:

.. code-block::  bash

    sudo tee /etc/systemd/system/codecarbon.service <<EOF
    [Unit]
    Description=CodeCarbon service
    After=network.target

    [Service]
    User=codecarbon
    Group=codecarbon
    WorkingDirectory=/opt/codecarbon
    ExecStart=/opt/codecarbon/.venv/bin/codecarbon monitor
    Restart=always

    [Install]
    WantedBy=multi-user.target
    EOF

Give permissions to the ``codecarbon`` group to read the RAPL (Running Average Power Limit) information:

.. code-block::  bash

    sudo chown -R root:codecarbon /sys/class/powercap/intel-rapl/*
    sudo chmod g+r -R /sys/class/powercap/intel-rapl/*

    sudo apt install sysfsutils
    echo "mode class/powercap/intel-rapl:0/energy_uj = 0440" >> /etc/sysfs.conf
    echo "owner class/powercap/intel-rapl:0/energy_uj = root:codecarbon" >> /etc/sysfs.conf

Create the configuration file for CodeCarbon:

.. code-block::  bash

    sudo tee /opt/codecarbon/.codecarbon.config <<EOF
    [codecarbon]
    api_endpoint = https://api.codecarbon.io
    organization_id = <organization_id>
    project_id = <project_id>
    experiment_id = <experiment_id>
    api_key = <api_key>
    # Verbose logging
    log_level=WARNING
    # Measure power every 30 seconds
    measure_power_secs=30
    # Send measure to API every 5 minutes (10*30 seconds)
    api_call_interval=10
    EOF

Enable and start the service:

.. code-block::  bash

    sudo systemctl enable codecarbon
    sudo systemctl start codecarbon

Check the traces of the service:

.. code-block::  bash

    journalctl -u codecarbon


You are done, CodeCarbon is now running as a service on your machine.

Wait 5 minutes for the first measure to be send to the dashboard at https://dashboard.codecarbon.io/.


Deploy CodeCarbon CLI as a Service using Ansible
````````````````````````````````````````````````

This section describes how to deploy CodeCarbon as a system service using Ansible automation.

It automate the manual installation done in the previous chapter.

What the Playbook Does
--------------------
The Ansible playbook automates the following tasks:

* Creates a dedicated system user and group for CodeCarbon
* Sets up a Python virtual environment
* Installs CodeCarbon package
* Configures RAPL permissions for power measurements
* Creates and configures the systemd service
* Sets up the CodeCarbon configuration file
* Starts and enables the service

Prerequisites
------------
* Ansible installed on your machine
* Debian-based target system(s)
* SSH access to target system(s)
* CodeCarbon API credentials from the dashboard

Directory Structure
-----------------
.. code-block:: text

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

Quick Start
----------

1. Set the the target to install in ``hosts``:

   .. code-block:: txt

       yourservername.yourdomain.com   hostname=yourservername ansible_user=root ansible_ssh_private_key_file=~/.ssh/id_ed25519

2. Update the variables in ``vars/main.yml`` with your configuration:

   .. code-block:: yaml

       organization_id: your_org_id
       project_id: your_project_id
       experiment_id: your_experiment_id
       api_key: your_api_key


3. Run the playbook:

   .. code-block:: bash

       ansible-playbook -i hosts tasks/main.yml


