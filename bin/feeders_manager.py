#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import time
from subprocess import Popen

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from vulnerabilitylookup.default.helpers import get_socket_path, tcp_cache_connect
from vulnerabilitylookup.helpers import get_feeders


FEEDERS = get_feeders()


def check_pids(r: Redis[str]) -> None:
    for name in FEEDERS:
        for pid in r.smembers(f"service|{name}"):
            try:
                os.kill(int(pid), 0)
            except OSError:
                print(f"Got a dead script: {name} - {pid}")
                r.srem(f"service|{name}", pid)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the feeders.")
    start_stop_group = parser.add_mutually_exclusive_group(required=True)
    start_stop_group.add_argument(
        "--start", action="store_true", help="Start all the feeders."
    )
    start_stop_group.add_argument(
        "--stop", action="store_true", help="Stop all the feeders"
    )
    parser.add_argument(
        "--reimport",
        default=False,
        action="store_true",
        help="Reimport all the feeders",
    )
    args = parser.parse_args()

    if args.start:
        if not FEEDERS:
            raise Exception("No feeder enabled.")
        for feeder_name, feeder_config in FEEDERS.items():
            print(f"Start {feeder_name}…")
            to_run = [feeder_config["script_name"]]
            if args.reimport:
                to_run.append("--reimport")
            Popen(to_run)
            print("Done.")
    elif args.stop:
        try:
            r = tcp_cache_connect()
        except RedisConnectionError:
            r = Redis(
                unix_socket_path=get_socket_path("cache"), db=1, decode_responses=True
            )
        # get the list of running scripts, find the feeders, set the shutdown key
        to_wait = set()
        for name in FEEDERS.keys():
            if r.exists(f"service|{name}"):
                r.set(f"{name}_shutdown", 1)
                to_wait.add(name)
        time.sleep(5)
        while to_wait:
            still_going = {
                name for name in FEEDERS.keys() if r.exists(f"service|{name}")
            }
            to_wait &= still_going
            if to_wait:
                print(f'Waiting for {", ".join(to_wait)} to finish')
                check_pids(r)
                time.sleep(1)
        print("All feeders stopped.")


if __name__ == "__main__":
    main()
