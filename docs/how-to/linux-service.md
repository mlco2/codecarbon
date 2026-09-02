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

### Step 3: Get Your Dashboard Credentials

Go to <https://dashboard.codecarbon.io/> and create an account.

Run the login and configuration wizard **as your own user**, not as the `codecarbon`
service user: `codecarbon login` needs a web browser and writes a `credentials.json`
file in the current directory, two things the service user does not have. The service
itself never uses those credentials, only the `api_key` you will write in its
configuration file at Step 6.

From your own account, in a directory you can write to:

``` bash
pip install codecarbon  # or run it with `uvx codecarbon`
codecarbon login
codecarbon config
```

`codecarbon config` asks you to pick or create an organization, a project and an
experiment, then writes their ids and an API key to `~/.codecarbon.config`. Keep that
file at hand, you will copy its values into the service configuration at Step 6.

If the machine has no browser (headless server), `codecarbon login` prints the
authentication URL: open it in a browser on the same machine, or forward the callback
port over SSH with `ssh -L 8090:localhost:8090 user@server` and open the URL on your
laptop, so that the `http://localhost:8090/callback` redirect reaches the CLI.

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

A `udev` rule restores those permissions on every boot, for all RAPL domains. Only the
`energy_uj` counters are touched, and only the `codecarbon` group gains read access:

``` bash
sudo tee /etc/udev/rules.d/99-codecarbon-rapl.rules <<'EOF'
SUBSYSTEM=="powercap", ACTION=="add", TEST=="energy_uj", \
  RUN+="/bin/chgrp codecarbon /sys%p/energy_uj", \
  RUN+="/bin/chmod 0440 /sys%p/energy_uj"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=powercap --action=add
```

Check that the counters are now readable by the `codecarbon` group:

``` bash
ls -l /sys/class/powercap/*/energy_uj
```

Energy counters are a side channel (see [Enable RAPL](enable-rapl.md) for the security
rationale and for the `sysfsutils` alternative). Keeping them restricted to the service
group means no other local account gains anything from this change.

### Step 6: Create the CodeCarbon Configuration File

Copy the ids and the API key from the `~/.codecarbon.config` written at Step 3 into the
service configuration file:

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