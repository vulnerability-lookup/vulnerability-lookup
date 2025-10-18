#!/usr/bin/env python3

from __future__ import annotations

import argparse

import logging.config

from vulnerabilitylookup.default import AbstractManager, get_config
from vulnerabilitylookup.feeders.csaf_abb import CSAFAbb

logging.config.dictConfig(get_config('logging'))


class CSAFAbbImporter(AbstractManager):

    def __init__(self, loglevel: int | None=None, *, reimport: bool=False) -> None:
        self.script_name = 'csaf_abb_importer'
        super().__init__(loglevel)
        self.csaf = CSAFAbb(reimport=reimport)

    def _to_run_forever(self) -> None:
        self.csaf.update(self.shutdown_requested)


def main() -> None:
    parser = argparse.ArgumentParser(description='Import CSAF ABB data.')
    parser.add_argument('--reimport', default=False, action='store_true', help='Reimport all data')
    args = parser.parse_args()
    c = CSAFAbbImporter(reimport=args.reimport)
    c.run(sleep_in_sec=3600)


if __name__ == '__main__':
    main()
