Feed syndication
================

Available feeds
---------------

.. list-table:: Available feeds
   :widths: 25 25 25 25
   :header-rows: 1

   * - Endpoint
     - Methods
     - Rule
     - Comment

   * - bundles_bp.feed_bundles
     - GET
     - /bundles/feed.<string:format>[?user=<login>]
     - Recent bundles.

   * - comments_bp.feed_comments
     - GET
     - /comments/feed.<string:format>[?user=<login>]
     - Recent comments.

   * - user_bp.feed_activity
     - GET
     - /user/<string:login>.<string:format>
     - Recent user activity.

   * - home_bp.feed_recent
     - GET
     - /recent/<string:source>.<string:format>[?vulnerability=<vuln-id>][?vendor=<vendor-id>]
     - Recent vulnerabilities per source or for all sources.

       Argument ``vulnerability`` is used to generate a feed of linked vulnerabilities.

       Argument ``vendor`` is used to generate a feed of vulnerabilities for the specified vendor.

   * - sightings_bp.feed_sightings
     - GET
     - /sightings/feed.<string:format>
     - Recent sightings.

   * - sightings_bp.feed_cpe_search
     - GET
     - /sightings/cpesearch/<string:cpe>/feed.<string:format>
     - Recent sightings for all vulnerabilities related to a CPE.


The value of ``format`` can be ``rss`` or ``atom``.

The value of ``source`` can be one of the following:
"all",
"github",
"cvelistv5",
"nvd",
"pysec",
"gsd",
"ossf_malicious_packages",
"csaf_certbund",
"csaf_siemens",
"csaf_redhat",
"csaf_cisa",
"csaf_cisco",
"csaf_sick",
"csaf_nozominetworks",
"csaf_ox",
"jvndb",
"tailscale",
"variot".


Examples
--------

Recent vulnerabilities from all sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    $ curl https://vulnerability.circl.lu/recent/all.atom


Recent vulnerabilities from pysec
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    $ curl https://vulnerability.circl.lu/recent/pysec.atom


Recent vulnerabilities related to a vendor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    $ curl 'https://vulnerability.circl.lu/recent/cvelistv5.atom?vendor=MISP&per_page=2&page=8'
    <?xml version='1.0' encoding='UTF-8'?>
    <feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en">
    <id>https://vulnerability.circl.lu/rss/recent/cvelistv5/2</id>
    <title>Most recent entries from cvelistv5</title>
    <updated>2024-11-26T08:02:41.668408+00:00</updated>
    <author>
        <name>Vulnerability-Lookup</name>
        <email>info@circl.lu</email>
    </author>
    <link href="https://vulnerability.circl.lu" rel="alternate"/>
    <generator uri="https://lkiesow.github.io/python-feedgen" version="1.0.0">python-feedgen</generator>
    <subtitle>Contains only the most 2 recent entries.</subtitle>
    <entry>
        <id>https://vulnerability.circl.lu/vuln/cve-2021-37534</id>
        <title>cve-2021-37534</title>
        <updated>2024-11-26T08:02:41.670402+00:00</updated>
        <link href="https://vulnerability.circl.lu/vuln/cve-2021-37534"/>
    </entry>
    <entry>
        <id>https://vulnerability.circl.lu/vuln/cve-2022-29528</id>
        <title>cve-2022-29528</title>
        <updated>2024-11-26T08:02:41.670364+00:00</updated>
        <link href="https://vulnerability.circl.lu/vuln/cve-2022-29528"/>
    </entry>
    </feed>



Recent vulnerabilities linked to the specified vulnerability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    $ curl 'https://vulnerability.circl.lu/recent/all.atom?vulnerability=cve-2021-22280'
    <?xml version='1.0' encoding='UTF-8'?>
    <feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en">
    <id>https://vulnerability.circl.lu/rss/recent/all/10</id>
    <title>Most recent entries from all</title>
    <updated>2024-11-26T08:03:09.000211+00:00</updated>
    <author>
        <name>Vulnerability-Lookup</name>
        <email>info@circl.lu</email>
    </author>
    <link href="https://vulnerability.circl.lu" rel="alternate"/>
    <generator uri="https://lkiesow.github.io/python-feedgen" version="1.0.0">python-feedgen</generator>
    <subtitle>Contains only the most 10 recent entries.</subtitle>
    <entry>
        <id>https://vulnerability.circl.lu/vuln/ghsa-x53h-2cjp-mwcx</id>
        <title>ghsa-x53h-2cjp-mwcx</title>
        <updated>2024-11-26T08:03:09.013675+00:00</updated>
        <link href="https://vulnerability.circl.lu/vuln/ghsa-x53h-2cjp-mwcx"/>
    </entry>
    <entry>
        <id>https://vulnerability.circl.lu/vuln/gsd-2021-22280</id>
        <title>gsd-2021-22280</title>
        <updated>2024-11-26T08:03:09.013602+00:00</updated>
        <link href="https://vulnerability.circl.lu/vuln/gsd-2021-22280"/>
    </entry>
    </feed>


Subscribing to the activity related to a vulnerability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The request will return recent observations (sightings) related to a vuln.

.. code-block:: bash

    $ curl 'https://vulnerability.circl.lu/sightings/feed.atom?vulnerability=CVE-2024-0012'



Recent sightings related to a product
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

        $ curl 'https://vulnerability.circl.lu/sightings/cpesearch/cpe:2.3:a:fortinet:forticlient_enterprise_management_server:*:*:*:*:*:*:*:*/feed.atom'


This will return recent sightings related to all CVEs for the specified product (identified by its CPE identifier).
Sightings are based on information from various trusted sources, including security websites, Exploit-DB.com, GitHub repositories, security blogs, social networks, and MISP.
