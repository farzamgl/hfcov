import numpy as np
import os
import subprocess
from subprocess import PIPE
import json

def cascade_run(name, probs):
  json_str = json.dumps(probs)
  print(subprocess.run(['make', str(name)+'.cascade', 'PROBS='+json_str], capture_output=False, text=True).stdout)

def clean_sim():
  print(subprocess.run(['make', 'clean'], capture_output=False, text=True).stdout)

def run_sim(name):
  print(subprocess.run(['make', str(name)+'.run'], capture_output=False, text=True).stdout)

def reward_cov(name, best):
  return int(subprocess.run(['make', str(name)+'.reward', 'BEST='+str(best)], capture_output=False, text=True).stdout)

def update_cov(name, best):
  subprocess.run(['make', str(name)+'.update', 'BEST='+str(best)], capture_output=False, text=True).stdout
