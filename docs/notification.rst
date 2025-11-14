Notification service
====================

This section provides instructions for activating the email notification service.


Launching the service with poetry
---------------------------------

From the directory used to install Vulnerability-Lookup:

.. code-block:: bash

    poetry run flask --app website.app notify_users



Launching the service with systemd
----------------------------------


Create the file ``/etc/systemd/system/vulnerability-lookup-notify.service``:

.. code-block:: ini

    [Unit]
    Description=Vulnerability-Lookup notification service
    After=vulnerability-lookup-web.service
    Requires=vulnerability-lookup-web.service

    [Service]
    Type=simple
    User=<system user used to install Vulnerability-Lookup>
    Group=<group of the user used to install Vulnerability-Lookup>
    WorkingDirectory=<path to the cloned repository>
    Environment="PATH=<path-to-virtualenv>/bin:/home/<user>/.local/bin:/usr/bin"
    Environment="VULNERABILITYLOOKUP_HOME=<path to the cloned repository>"
    ExecStart=/bin/bash -lc "poetry run flask --app website.app notify_users"
    StandardOutput=append:/var/log/vulnerability-lookup_notify_message.log
    StandardError=append:/var/log/vulnerability-lookup_notify_error.log
    Restart=on-failure
    RestartSec=15s

    [Install]
    WantedBy=multi-user.target


.. note::

    Adjust the variables appropriately.


Then reload and enable the service:

.. code-block:: bash

    sudo systemctl daemon-reload
    sudo systemctl enable vulnerability-lookup-notify.service
    sudo systemctl start vulnerability-lookup-notify.service
    systemctl status vulnerability-lookup-notify.service


To follow the service logs live:

.. code-block:: bash

    sudo journalctl -u vulnerability-lookup-notify.service -f

Error logs:

.. code-block:: bash

    tail -f logs/vulnerability-lookup_notify_error.log


Messages:

.. code-block:: bash

    tail -f logs/vulnerability-lookup_notify_message.log
