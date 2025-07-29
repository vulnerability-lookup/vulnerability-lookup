#!/usr/bin/env python3

from __future__ import annotations

import argparse

import logging.config

from vulnerabilitylookup.default import AbstractManager, get_config
from vulnerabilitylookup.feeders.gcve_vl import GCVE

logging.config.dictConfig(get_config('logging'))


class GCVEImporter(AbstractManager):

    def __init__(self, loglevel: int | None=None, *, reimport: bool=False) -> None:
        self.script_name = 'gcve_vl_importer'
        super().__init__(loglevel)
        self.gcve = GCVE(reimport=reimport)

    def _to_run_forever(self) -> None:
        self.gcve.update(self.shutdown_requested)


def main() -> None:
    parser = argparse.ArgumentParser(description='GCVE Vulnerability Lookup Importer')
    parser.add_argument('--reimport', action='store_true', help='Reimport all data')
    args = parser.parse_args()
    jvn = GCVEImporter(reimport=args.reimport)
    jvn.run(sleep_in_sec=3600)


if __name__ == '__main__':
    main()
