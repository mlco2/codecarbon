.. _installation:

Installing CodeCarbon
=====================

From pypi repository
--------------------

The package is hosted on the pip repository `here <https://pypi.org/project/codecarbon/>`_.

To install the package, run the following command in your terminal.

.. code-block::  bash

    pip install codecarbon

From conda repository
--------------------

The package is hosted on the conda repository `here <https://anaconda.org/codecarbon/codecarbon>`_.

To install the package, run the following command in your terminal.

.. code-block::  bash

    conda install -c codecarbon -c conda-forge codecarbon

..  note::

    We recommend using Python 3.6 or above.


Dependencies
------------

pip
~~~
The following pip packages are used by the CodeCarbon package, and will be installed along with the package itself:

.. code-block::  bash

    APScheduler
    co2-tracker-utils
    dash
    dash_bootstrap_components
    dataclasses
    fire
    pandas
    pynvml
    requests
