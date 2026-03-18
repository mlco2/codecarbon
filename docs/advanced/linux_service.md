# Install CodeCarbon as a Linux service

To install CodeCarbon as a Linux service, follow the instructions below.
It works on Ubuntu or other Debian-based systems using systemd.

Create a dedicated user:

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

Create a virtual environment for CodeCarbon :

``` bash
sudo apt install python3-venv
sudo -u codecarbon python3 -m venv /opt/codecarbon/.venv
```

Install CodeCarbon in the virtual environment:

``` bash
sudo -u codecarbon /opt/codecarbon/.venv/bin/pip install codecarbon
```

Go to <https://dashboard.codecarbon.io/> and create an account to get
your API key.

Configure CodeCarbon:

``` bash
sudo -u codecarbon /opt/codecarbon/.venv/bin/codecarbon login
```

Create a systemd service file:

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

Give permissions to the `codecarbon` group to read the RAPL (Running
Average Power Limit) information:

``` bash
sudo chown -R root:codecarbon /sys/class/powercap/intel-rapl/*
sudo chmod g+r -R /sys/class/powercap/intel-rapl/*

sudo apt install sysfsutils
echo "mode class/powercap/intel-rapl:0/energy_uj = 0440" >> /etc/sysfs.conf
echo "owner class/powercap/intel-rapl:0/energy_uj = root:codecarbon" >> /etc/sysfs.conf
```

Create the configuration file for CodeCarbon:

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

Enable and start the service:

``` bash
sudo systemctl enable codecarbon
sudo systemctl start codecarbon
```

Check the traces of the service:

``` bash
journalctl -u codecarbon
```

You are done, CodeCarbon is now running as a service on your machine.

Wait 5 minutes for the first measure to be send to the dashboard at
<https://dashboard.codecarbon.io/>.