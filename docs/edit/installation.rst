.. _installation:

Installing CodeCarbon
=====================

Create a virtual environment using `conda` for easier management of dependencies and packages.
For installing conda, follow the instructions on the
`official conda website <https://docs.conda.io/projects/conda/en/latest/user-guide/installl>`__

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

    We recommend using Python 3.7 or above.


Dependencies
------------

pip
~~~
The following pip packages are used by the CodeCarbon package, and will be installed along with the package itself:

.. code-block::  bash

    arrow
    click
    dash
    dash_bootstrap_components
    dataclasses
    fire
    pandas
    psutil
    pynvml
    py-cpuinfo
    requests
