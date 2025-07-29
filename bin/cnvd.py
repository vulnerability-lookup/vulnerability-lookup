#!/usr/bin/env python3

from __future__ import annotations

import argparse

import logging.config

from vulnerabilitylookup.default import AbstractManager, get_config
from vulnerabilitylookup.feeders.cnvd import CNVD

logging.config.dictConfig(get_config('logging'))


class CNVDImporter(AbstractManager):

    def __init__(self, loglevel: int | None=None, *, reimport: bool=False) -> None:
        self.script_name = 'cnvd_importer'
        super().__init__(loglevel)
        self.cnvd = CNVD(reimport=reimport)

    def _to_run_forever(self) -> None:
        self.cnvd.update(self.shutdown_requested)


def main() -> None:
    parser = argparse.ArgumentParser(description='CNVD Importer')
    parser.add_argument('--reimport', default=False, action='store_true', help='Reimport all data')
    args = parser.parse_args()
    gsd = CNVDImporter(reimport=args.reimport)
    gsd.run(sleep_in_sec=3600)


if __name__ == '__main__':
    main()
