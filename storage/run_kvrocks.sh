#!/bin/bash

set -e
set -x

if [ -f ../../kvrocks/build/kvrocks ]; then
    ../../kvrocks/build/kvrocks -c kvrocks.conf
elif [ -x "$(command -v kvrocks)" ]; then
    echo 'kvrocks does not seem to be built locally, using the system-wide install instead.'
    kvrocks -c kvrocks.conf
else
    echo 'kvrocks does not seem to be installed locally, using docker instead.'
    echo 'We assume you have docker installed in rootless mode, following the instructions here: https://docs.docker.com/engine/security/rootless/'
    echo 'If you have docker installed in normal mode, add sudo in front of the command below'
    docker run -d -it -p10002:10002 -v ./:/kvrocks/conf:rw apache/kvrocks --bind 0.0.0.0 --config /kvrocks/conf/kvrocks.conf
fi
