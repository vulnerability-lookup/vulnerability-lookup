#!/usr/bin/env python3

from __future__ import annotations

import argparse

import logging.config

from vulnerabilitylookup.default import AbstractManager, get_config
from vulnerabilitylookup.feeders.emb3d import emb3d

logging.config.dictConfig(get_config('logging'))


class emb3dImporter(AbstractManager):

    def __init__(self, loglevel: int | None=None, *, reimport: bool=False) -> None:
        self.script_name = 'emb3d_importer'
        super().__init__(loglevel)
        self.emb3d = emb3d(reimport=reimport)

    def _to_run_forever(self) -> None:
        self.emb3d.update(self.shutdown_requested)


def main() -> None:
    parser = argparse.ArgumentParser(description='Emb3d Importer')
    parser.add_argument('--reimport', default=False, action='store_true', help='Reimport all data')
    args = parser.parse_args()
    gsd = emb3dImporter(reimport=args.reimport)
    gsd.run(sleep_in_sec=3600)


if __name__ == '__main__':
    main()
