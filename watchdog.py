#!/bin/python3

import toml
import sys
import signal
import time
import subprocess
import functools

def run_cmd(cmd):
  return subprocess.run(['bash', '-c', cmd], capture_output=True)

def exec_actions(type, actions):
  for action in actions:
    cmd = action['cmd']

    result = run_cmd(cmd)
    if result.returncode != 0:
      print('[WARNING ] {} action "{}" failed with return code {}: {}'
          .format(type, cmd, result.returncode, result.stdout.decode()))

def watchdog(config):
  interval = config['check']['interval']
  check_cmd = config['check']['cmd']

  def get_actions(name):
    return config[name] if name in config else []

  rise = get_actions('rise')
  fall = get_actions('fall')
  high = get_actions('high')
  low = get_actions('low')

  print('[INFO    ] ================ [start] ================')

  last_state = True

  while True:
    result = run_cmd(check_cmd)
    if result.returncode != 0:
      print('[WARNING ] check failed with return code {}: {}'
          .format(result.returncode, result.stdout.decode()))
      
      if last_state == True:
        exec_actions('fall', fall)
      exec_actions('low', low)

      last_state = False
    else:
      if last_state == False:
        print('[INFO    ] status recovered')
        exec_actions('rise', rise)
      exec_actions('high', high)

      last_state = True

    time.sleep(interval)

def main():
  if len(sys.argv) != 2:
    print('[ERROR   ] Wrong numbers of parameters. Usage: {} <config.toml>'
        .format(sys.argv[0]))
    exit(1)

  watchdog(toml.loads(open(sys.argv[1], 'r').read()))

def drop():
  print('[INFO    ] ================ [stop ] ================')
  exit(0)

def app(fn):
  try:
    global print
    print = functools.partial(print, flush=True)

    def handler(x, y):
      drop()

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)

    fn()
  except KeyboardInterrupt:
    drop()
  except Exception as e: 
    print('[ERROR   ] internal exception: {}'.format(e))
    exit(1)

if __name__ == '__main__':
  app(main)
