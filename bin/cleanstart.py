#!/usr/bin/env python3

from __future__ import annotations

import argparse

import logging.config

from vulnerabilitylookup.default import AbstractManager, get_config
from vulnerabilitylookup.feeders.cleanstart import Cleanstart

logging.config.dictConfig(get_config('logging'))


class CleanstartImporter(AbstractManager):

    def __init__(self, loglevel: int | None=None, *, reimport: bool=False) -> None:
        self.script_name = 'cleanstart_importer'
        super().__init__(loglevel)
        self.fetcher = Cleanstart(reimport=reimport)

    def _to_run_forever(self) -> None:
        self.fetcher.update(self.shutdown_requested)


def main() -> None:
    parser = argparse.ArgumentParser(description='Cleanstart Importer')
    parser.add_argument('--reimport', default=False, action='store_true', help='Reimport all data')
    args = parser.parse_args()
    nm = CleanstartImporter(reimport=args.reimport)
    nm.run(sleep_in_sec=3600)


if __name__ == '__main__':
    main()
