.. _installation:

Installing CodeCarbon
=====================

Create a virtual environment using `conda` for easier management of dependencies and packages.
For installing conda, follow the instructions on the
`official conda website <https://docs.conda.io/projects/conda/en/latest/user-guide/install>`__

.. code-block::  bash

    conda create --name codecarbon
    conda activate codecarbon

From PyPi repository
--------------------

The package is hosted on the pip repository `here <https://pypi.org/project/codecarbon/>`_.

To install the package, run the following command in your terminal.

.. code-block::  bash

    pip install codecarbon

From conda repository
---------------------

The package is hosted on the conda repository `here <https://anaconda.org/codecarbon/codecarbon>`_.

To install the package, run the following command in your terminal.

.. code-block::  bash

    conda install -c codecarbon -c conda-forge codecarbon

..  note::

    We recommend using Python 3.8 or above.


Dependencies
------------

The following packages are used by the CodeCarbon package, and will be installed along with the package itself:

.. code-block::  bash

    arrow
    click
    fief-client[cli]
    pandas
    prometheus_client
    psutil
    py-cpuinfo
    pynvml
    rapidfuzz
    requests
    questionary
    rich
    typer


Please refer to `pyproject.toml <https://github.com/mlco2/codecarbon/blob/master/pyproject.toml>`_ for the latest list of the packages used.

Install CodeCarbon as a Linux service
-------------------------------------

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
    Environment="CODECARBON_API_KEY=YOUR_API_KEY"
    ExecStart=/opt/codecarbon/.venv/bin/codecarbon monitor
    Restart=always

    [Install]
    WantedBy=multi-user.target
    EOF

Replace YOUR_API_KEY with the API key you obtained from the CodeCarbon dashboard.

Enable and start the service:

.. code-block::  bash

    sudo systemctl enable codecarbon
    sudo systemctl start codecarbon

Check the status of the service:

.. code-block::  bash

    sudo systemctl status codecarbon

You should see the service running.

To stop the service:

.. code-block::  bash

    sudo systemctl stop codecarbon


Optionaly, you can also give permissions to the user to read the RAPL information:

.. code-block::  bash

    sudo chown -R root:codecarbon /sys/class/powercap/intel-rapl

    sudo apt install sysfsutils
    echo "mode class/powercap/intel-rapl:0/energy_uj = 0440" >> /etc/sysfs.conf
    echo "owner class/powercap/intel-rapl:0/energy_uj = root:codecarbon" >> /etc/sysfs.conf

