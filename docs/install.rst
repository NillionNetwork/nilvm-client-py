Install Python Client
=====================

**Nillion Python Client** runs on Python ``3.8``, ``3.9``, ``3.10``,  ``3.11``, and ``3.12`` and on several platforms (linux, windows, osx[intel|arm]). In addition to other SDK tools, you may be interested in writing Nillion's nada_lang compute programs which is a python based language.

Some good practices to follow for options below are:

- Use new and isolated Virtual Environments for each project (`virtualenv <https://virtualenv.pypa.io/en/latest/user_guide.html>`_).
- On Notebooks, always restart your kernel after installations.

Install Nillion Python Client
=============================

PyPI (pip)
----------

    >>> pip install nillion-client nada-dsl 

Using a virtualenv
------------------

As a python package, we recommended to install the libs in a virtualenv.

.. code-block:: bash
  
    virtualenv venv
    . ./venv/bin/activate
    pip install nillion-client nada-dsl nillion-python-helpers


