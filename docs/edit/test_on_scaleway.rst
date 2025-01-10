.. _test_on_scaleway:


Test of CodeCarbon on Scaleway hardware
=======================================

We use Scaleway hardware to test CodeCarbon on a real-world scenario. We use the following hardware:


    EM-I120E-NVME   Debian 12 (Bookworm)   AMD EPYC 8024P     64 GB    2 x 960 GB NVMe


Choose Ubuntu as OS because new version of stress-ng is not available on Debian 12 (Bookworm).

.. code-block:: console

    ssh ubuntu@195.154.100.236
    sudo apt update && sudo apt install -y git pipx python3-launchpadlib htop
    pipx ensurepath
    sudo add-apt-repository -y ppa:colin-king/stress-ng
    sudo apt update && sudo apt install -y stress-ng
    export PATH=$PATH:/home/ubuntu/.local/bin
    git clone https://github.com/mlco2/codecarbon.git
    git checkout use-cpu-load
    cd codecarbon
    pipx install hatch
    hatch run python examples/compare_cpu_load_and_RAPL.py
