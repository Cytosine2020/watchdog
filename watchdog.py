#!/bin/python3

import toml
import json
import sys
import signal
import time
import subprocess
import functools

def run_cmd(type, config, variables={}):
  cmd = config['cmd']
  
  if 'args' in config:
    args = ''
    for name in config['args']:
      if name in variables:
        args += '{}={}\n'.format(name, variables[name])
      else:
        args += '{}=\n'.format(name)
        print('[WARNING ] {} command "{}" argument "{}" not set'
            .format(type, cmd, name))
    cmd = args + cmd

  result = subprocess.run(['bash', '-c', cmd], capture_output=True)

  if result.returncode == 0:
    if 'ret' in config:      
      try:
        ret = json.loads(result.stdout.decode())
      except Exception as e: 
        print('[ERROR   ] internal exception: {}'.format(e))
        exit(1)
      
      for name in config['ret']:
        if name in ret:
          variables[name] = ret[name]
        else:
          print('[WARNING ] {} command "{}" does not output variable "{}"'
              .format(type, cmd, name))
  else:
    print('[WARNING ] {} command "{}" failed with return code {}: {}'
        .format(type, cmd, result.returncode, result.stdout.decode()))

  return result.returncode == 0

def watchdog(config):
  interval = config['check']['interval']
  check = config['check']

  def get_actions(name):
    return config[name] if name in config else []

  rise = get_actions('rise')
  fall = get_actions('fall')
  high = get_actions('high')
  low = get_actions('low')

  print('[INFO    ] ================ [start] ================')

  last_state = True

  for config in low:
    run_cmd('low', config)

  while True:
    if run_cmd('check', check):      
      if last_state == False:
        for config in rise:
          run_cmd('rise', config)
      
      for config in high:
        run_cmd('high', config)

      last_state = True
    else:
      if last_state == True:
        for config in fall:
          run_cmd('fall', config)

      for config in low:
        run_cmd('low', config)

      last_state = False

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
