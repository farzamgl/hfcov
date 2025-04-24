import numpy as np
import os
import subprocess
from subprocess import PIPE
import json

def cascade_run(name, probs):
  print('Running Cascade: ' + str(name))
  json_str = json.dumps(probs)
  subprocess.run(['make', '-s', str(name)+'.cascade', 'PROBS='+json_str], stdout = subprocess.DEVNULL)

def clean_sim():
  print(subprocess.run(['make', '-s', 'clean'], capture_output=False, text=True).stdout)

def run_sim(name):
  print('Running ZP sim: ' + str(name))
  subprocess.run(['make', '-s', str(name)+'.run'], stdout = subprocess.DEVNULL)

def reward_cov(name, best):
  return int(subprocess.run(['make', '-s', str(name)+'.reward', 'BEST='+str(best)], capture_output=True, text=True).stdout)

def update_cov(name, best):
  subprocess.run(['make', '-s', str(name)+'.update', 'BEST='+str(best)], capture_output=False, text=True).stdout

def get_craw(name):
  return int(subprocess.run(['make', '-s', str(name)+'.craw'], capture_output=True, text=True).stdout)

def get_calign(name):
  return int(subprocess.run(['make', '-s', str(name)+'.calign'], capture_output=True, text=True).stdout)

def get_ctoggle(name):
  return int(subprocess.run(['make', '-s', str(name)+'.ctoggle'], capture_output=True, text=True).stdout)

def rm_dir(name):
  subprocess.run(['make', '-s', str(name)+'.rm'], capture_output=False, text=True).stdout
