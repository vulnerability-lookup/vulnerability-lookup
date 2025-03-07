#!/usr/bin/env python3

from __future__ import annotations

import argparse
import logging
import logging.config
import shlex
import subprocess
import sys

from vulnerabilitylookup.default import get_homedir, get_config

logging.config.dictConfig(get_config('logging'))


def keep_going(ignore: bool=False) -> None:
    if ignore:
        return
    keep_going = input('Continue? (y/N) ')
    if keep_going.lower() != 'y':
        print('Okay, quitting.')
        sys.exit()


def run_command(command: str, expect_fail: bool=False, capture_output: bool=True, cwd: str="") -> None:
    args = shlex.split(command)
    if cwd == "":
        cwd = get_homedir().absolute().as_posix()
    process = subprocess.run(args, cwd=cwd, capture_output=capture_output)
    if capture_output:
        print(process.stdout.decode())
    if process.returncode and not expect_fail:
        print(process.stderr.decode())
        sys.exit()


def main() -> None:
    parser = argparse.ArgumentParser(description='Completely delete all the feeds.')
    parser.parse_args()

    print('* Stop services:')
    keep_going()
    print('Please be patient...')
    run_command('stop')
    print('Stopped.')

    print('We will now delete the database containing the imported feeds, the website will be empty until they are reimported, which can take a while.')
    print('* Do you want to do that?')
    keep_going()
    kvrocks_data = get_homedir() / 'storage'
    for root, dirs, files in (kvrocks_data / 'db').walk(top_down=False):
        for name in files:
            (root / name).unlink()
        for name in dirs:
            (root / name).rmdir()
    (get_homedir() / 'cache' / 'dump.rdb').unlink(missing_ok=True)

    print('* Update vulnerability lookup and the git repositories of the feeds?')
    keep_going()
    print('Please be patient...')
    run_command('git stash')
    run_command('git submodule init')
    run_command('git pull --tags --recurse-submodules')
    run_command('git stash apply')

    print('Done. You can now restart the services, and wait for the feeds to be imported.')


if __name__ == '__main__':
    main()
