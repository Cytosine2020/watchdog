#!/bin/sh

if [ ! -z $(which apt) ]; then
  apt install -y python3 python3-pip || exit 1
elif [ ! -z $(which yum) ]; then
  yum install -y python3 python3-pip || exit 1
fi

python3 -m pip install toml || exit 1

if [ -f /usr/local/bin/watchdog.py ]; then
  echo "Already installed, please uninstall first to reinstall!"
  exit 1
fi

cp -n watchdog.py /usr/local/bin/
