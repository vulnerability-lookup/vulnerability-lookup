Updating the application
========================

To update Vulnerability-Lookup, run:

.. code-block:: bash

    $ cd vulnerability-lookup/
    $ poetry run update

During the update process, you will be prompted to back up the PostgreSQL database.
If you prefer to trigger the backup manually, use:

.. code-block:: bash

    $ poetry run flask --app website.app db_backup


Updating the Kvrocks indexes
----------------------------

If you need to rebuild the Kvrocks indexes, run:

.. code-block:: bash

    $ cd vulnerability-lookup/
    $ poetry run python bin/index_vulnerabilities.py
    $ poetry run python bin/index_cwe.py
