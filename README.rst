configset
==================

simple write config/setting, wrap of configparser


Installing
----------

Install and update using `pip`_:

.. code-block:: text

    $ pip install configset

configset supports Python 2 and newer, Python 3 and newer, and PyPy.

.. _pip: https://pip.pypa.io/en/stable/quickstart/


Example
----------------

What does it look like? Here is an example of a simple configset program:

.. code-block:: python

    import configset
    
    class pcloud(object):

        def __init__(self, **kwargs):
            ...
            self.CONFIG = configset.configset()
            self.CONFIG.configname = os.path.join(os.path.dirname(__file__), 'pcloud.ini')
            ...

            self.username = self.CONFIG.read_config('AUTH', 'username', value="admin")
            self.password = self.CONFIG.read_config('AUTH', 'password', value="12345678")
            ...

Support
------

*   Python 2.7 +, Python 3.x
*   Windows, Linux

Links
-----

*   License: `BSD <https://bitbucket.org/licface/configset/src/default/LICENSE.rst>`_
*   Code: https://bitbucket.org/licface/configset
*   Issue tracker: https://bitbucket.org/licface/configset/issues