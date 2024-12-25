import numpy as np
import os
import subprocess
from subprocess import PIPE
import json

def cascade_run(test, probs):
  # TODO: fix the Cascade run to generate and return nbf
  json_str = json.dumps(probs)
  print(subprocess.run(['make', str(test)+'.cascade', 'PROBS='+json_str], capture_output=False, text=True).stdout)

def clean_sim():
  print(subprocess.run(['make', 'clean'], capture_output=False, text=True).stdout)

def run_sim(test, nbf_file):
  print(subprocess.run(['make', str(test)+'run', 'NBF_FILE='+str(nbf_file)], capture_output=False, text=True).stdout)

def reward_cov(test):
  return int(subprocess.run(['make', str(test)+'.reward',], capture_output=False, text=True).stdout)

def update_cov(test):
  subprocess.run(['make', str(test)+'.update',], capture_output=False, text=True).stdout

def fuzz_run(test, probs):
  # create an elf with input probs
  nbf_file = cascade_run(test, probs)
  # run verilator sim and gather coverage files
  run_sim(test, nbf_file)
  # calculate reward based on comparing with previous best coverage
  reward = reward_cov(test)
  # update best coverage
  update_cov(test)
  return reward
