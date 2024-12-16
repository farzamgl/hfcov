import numpy as np
import os
import subprocess
from subprocess import PIPE

def clean_sim():
  print(subprocess.run(['make', 'clean'], capture_output=False, text=True).stdout)

def run_sim(test):
  print(subprocess.run(['make', 'run', 'NBF_FILE='+test], capture_output=False, text=True).stdout)

def gather_cov(test):
  print(subprocess.run(['make', test+'.cov',], capture_output=False, text=True).stdout)

def reward_cov(test):
  return int(subprocess.run(['make', test+'.reward',], capture_output=False, text=True).stdout)

def update_cov(test):
  subprocess.run(['make', test+'.update',], capture_output=False, text=True).stdout

def fuzz_run(nbf):
  # get test name
  test = os.path.splitext(os.path.basename(nbf))[0]
  # run verilator sim
  run_sim(nbf)
  # gather raw and aligned coverage files
  gather_cov(test)
  # calculate reward based on comparing with previous best coverage
  reward = reward_cov(test)
  # update best coverage
  update_cov(test)
  return reward

