Vulnerability-Lookup
====================


.. only:: html

    .. image:: https://img.shields.io/github/release/vulnerability-lookup/vulnerability-lookup.svg?style=flat-square
        :alt: Latest release
        :target: https://github.com/vulnerability-lookup/vulnerability-lookup/releases/latest
        :class: img-responsive

    .. image:: https://img.shields.io/github/license/vulnerability-lookup/vulnerability-lookup.svg?style=flat-square
        :alt: License
        :target: https://github.com/vulnerability-lookup/vulnerability-lookup/blob/main/LICENSE.md
        :class: img-responsive

    .. image:: https://img.shields.io/github/stars/vulnerability-lookup/vulnerability-lookup.svg?style=flat-square
        :alt: Stars
        :target: https://github.com/vulnerability-lookup/vulnerability-lookup/stargazers
        :class: img-responsive

    .. image:: https://img.shields.io/github/contributors/vulnerability-lookup/vulnerability-lookup.svg?style=flat-square
        :alt: Contributors
        :target: https://github.com/vulnerability-lookup/vulnerability-lookup/graphs/contributors
        :class: img-responsive


.. toctree::
    :caption: Architecture
    :maxdepth: 3
    :hidden:

    architecture
    webservice
    streaming

.. toctree::
    :caption: Technical considerations
    :maxdepth: 3
    :hidden:

    prerequisites
    installation
    update
    notification
    command-line-interface
    logging

.. toctree::
    :caption: Usage
    :maxdepth: 3
    :hidden:

    feeds
    api-v1

.. toctree::
    :caption: Community
    :maxdepth: 3
    :hidden:

    contributing


Presentation
------------

`Vulnerability-Lookup <https://www.vulnerability-lookup.org>`_ facilitates quick correlation of vulnerabilities
from various sources, independent of vulnerability IDs, and streamlines the management of Coordinated Vulnerability Disclosure (CVD).
Vulnerability-Lookup is also a collaborative platform where users can comment on security advisories and create bundles.

A Vulnerability-Lookup instance operated by `CIRCL <https://www.circl.lu>`_ is available at https://vulnerability.circl.lu.

Features
~~~~~~~~

- **API**: A comprehensive and fast lookup API for searching vulnerabilities and identifying correlations by vulnerability identifier.
- **Feeders**: Modular system to import vulnerabilities from different sources.
- **CVD process**: Creation, edition and fork/copy of Security Advisories with the `vulnogram editor <https://github.com/Vulnogram>`_.
  Support of local vulnerability source per Vulnerability-Lookup instance.
- **Sightings**: Users have the possibility to add observations to vulnerabilities with different types of sightings, such as:
  *seen*, *exploited*, *not exploited*, *confirmed*, *not confirmed*, *patched*, and *not patched*.
- **Comments**: Ability to add, review and share comments on vulnerability advisories.
- **Bundles**: Possibility to create bundles of vulnerability advisories with a description.
- **RSS/Atom**: An extensive RSS and Atom support for vulnerabilities and comments.
- **EPSS**: Integration of the Exploit Prediction Scoring System.
- **Track vulnerabilities** effortlessly with product watch lists and email notifications.


.. image:: _static/img/vulnerability-lookup.png
   :alt: High level architecture
   :target: _static/img/vulnerability-lookup.png


Contributing
------------

If you are interested in contributing to Vulnerability-Lookup, take a look at
`the official repository <https://github.com/vulnerability-lookup/vulnerability-lookup>`_.


Contact
-------

`CIRCL - Computer Incident Response Center Luxembourg <https://www.circl.lu>`_ -
`info@circl.lu <info@circl.lu>`_


License
-------

Vulnerability-Lookup is licensed under
`GNU Affero General Public License version 3 <https://www.gnu.org/licenses/agpl-3.0.html>`_.
