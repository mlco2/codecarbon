# Install CodeCarbon as a Linux Service

This guide shows how to install and run CodeCarbon as a systemd service on Linux (Ubuntu or Debian-based systems). This allows CodeCarbon to continuously monitor your system's carbon emissions in the background.

## Prerequisites

- Ubuntu or Debian-based Linux system
- `sudo` access
- Python 3.8+

## Installation Steps

### Step 1: Create a Dedicated User

Create a system user for CodeCarbon to run under:

``` bash
sudo useradd -r -s /bin/false codecarbon
```

Create a directory for the CodeCarbon service:

``` bash
sudo mkdir /opt/codecarbon
```

Change the ownership of the directory to the user created above:

``` bash
sudo chown codecarbon:codecarbon /opt/codecarbon
```

### Step 2: Create a Virtual Environment

Create and activate a Python virtual environment for CodeCarbon:

``` bash
sudo apt install python3-venv
sudo -u codecarbon python3 -m venv /opt/codecarbon/.venv
```

Install CodeCarbon in the virtual environment:

``` bash
sudo -u codecarbon /opt/codecarbon/.venv/bin/pip install codecarbon
```

### Step 3: Authenticate with CodeCarbon

Go to <https://dashboard.codecarbon.io/> and create an account to get your API key. Then authenticate locally:

Configure CodeCarbon:

``` bash
sudo -u codecarbon /opt/codecarbon/.venv/bin/codecarbon login
```

### Step 4: Create a Systemd Service File

Create the service configuration file for systemd:

``` bash
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
```

### Step 5: Configure RAPL Permissions

Give the CodeCarbon user permissions to read RAPL (Running Average Power Limit) energy information for accurate CPU power tracking:

``` bash
sudo chown -R root:codecarbon /sys/class/powercap/intel-rapl/*
sudo chmod g+r -R /sys/class/powercap/intel-rapl/*

sudo apt install sysfsutils
echo "mode class/powercap/intel-rapl:0/energy_uj = 0440" >> /etc/sysfs.conf
echo "owner class/powercap/intel-rapl:0/energy_uj = root:codecarbon" >> /etc/sysfs.conf
```

### Step 6: Create the CodeCarbon Configuration File

Configure CodeCarbon with your dashboard credentials:

``` bash
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
```

### Step 7: Enable and Start the Service

Enable the CodeCarbon service to start on boot and start it now:

``` bash
sudo systemctl enable codecarbon
sudo systemctl start codecarbon
```

### Step 8: Verify the Service is Running

Check the service logs to confirm CodeCarbon is running correctly:

``` bash
journalctl -u codecarbon
```

## Verification

You are done! CodeCarbon is now running as a systemd service on your machine.

Wait 5 minutes for the first measurements to be sent to the dashboard at <https://dashboard.codecarbon.io/>. You should then see emissions data appearing on your dashboard.

## Next Steps

- [View Your Results](cloud-api.md) on the CodeCarbon dashboard
- [Configure CodeCarbon](configuration.md) to customize measurement intervals or other settings
- [Check the Linux service logs](https://www.digitalocean.com/community/tutorials/how-to-use-journalctl-to-view-system-logs-in-ubuntu-18-04) for troubleshooting