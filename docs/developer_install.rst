.. _developer_install:

=================
Developer Install
=================

.. important::

  The following commands will install *aquacrop_bmi_babel* into your current environment. Although
  not necessary, we **highly recommend** you install *aquacrop_bmi_babel* into its own
  :ref:`virtual environment <virtual_environments>`.

If you will be modifying code or contributing new code to *aquacrop_bmi_babel*, you will first
need to get *aquacrop_bmi_babel*'s source code and then install *aquacrop_bmi_babel* from that code.

Source Install
--------------

*aquacrop_bmi_babel* is actively being developed on GitHub, where the code is freely available.
If you would like to modify or contribute code, you can either clone our
repository

.. code-block:: bash

  git clone git://github.com/pymt-lab/aquacrop_bmi_babel.git

or download the `tarball <https://github.com/pihchikk/aquacrop_bmi_babel/tarball/master>`_
(a zip file is available for Windows users):

.. code-block:: bash

  curl -OL https://github.com/pihchikk/aquacrop_bmi_babel/tarball/master

Once you have a copy of the source code, you can install it into your current
Python environment,

.. tab:: mamba

  .. code-block:: bash

    cd aquacrop_bmi_babel
    mamba install --file=requirements.txt
    pip install -e .

.. tab:: conda

  .. code-block:: bash

    cd aquacrop_bmi_babel
    conda install --file=requirements.txt
    pip install -e .

.. tab:: pip

  .. code-block:: bash

    cd aquacrop_bmi_babel
    pip install -e .