import numpy as np
import sys
import os
import argparse
import pprint
import itertools

import fuzz

class EXP3:
    def __init__(self, arms, arm_probs, gamma, alpha, satw):
        """
        Initialize the EXP3 algorithm.
        """
        self.arms = arms
        self.arm_probs = arm_probs
        self.gamma = gamma
        self.alpha = alpha
        self.satw = satw
        self.weights = np.ones(arms)  # Initialize weights for each arm

        self.arm_pulls = [0] * self.arms
        self.arm_satcnt = [0] * self.arms
        self.pulls = []

    def select_arm(self):
        """
        Select an arm to pull based on the weighted probabilities.
        """
        probabilities = self.get_probabilities()
        return np.random.choice(self.arms, p=probabilities)

    def get_probabilities(self):
        """
        Calculate the probability distribution for selecting each arm.
        """
        total_weight = np.sum(self.weights)
        probabilities = (1 - self.gamma) * (self.weights / total_weight) + (self.gamma / self.arms)
        return probabilities

    def update(self, chosen_arm, reward):
        """
        Update the weights of the chosen arm based on the received reward.
        """
        probabilities = self.get_probabilities()
        estimated_reward = reward / probabilities[chosen_arm]
        self.weights[chosen_arm] *= np.exp(self.gamma * estimated_reward / self.arms)

    def step(self, itr, arm, probs):
      print('------------------------')
      print('Pulling arm: ' + str(arm))
      # create an nbf with input probs
      fuzz.cascade_run(itr, probs.tolist())

      # run verilator sim and gather coverage files
      fuzz.run_sim(itr)

      # calculate reward based on comparing with previous best coverage
      gcov = fuzz.reward_cov(itr, 'gbest')
      lcov = fuzz.reward_cov(itr, str(arm) + '.best')
      # only use global coverage as reward on first arm pull
      if self.arm_pulls[arm] == 0:
        reward = gcov
      else:
        reward = (self.alpha * lcov) + ((1 - self.alpha) * gcov)
      # using logistic function to normalize reward
      reward = (1 - np.exp(-0.25 *reward)) / (1 + np.exp(-0.25 * reward))
      print('gcov: ' + str(gcov))
      print('lcov: ' + str(lcov))
      print('reward: ' + str(reward))

      # update best coverage
      fuzz.update_cov(itr, 'gbest')
      fuzz.update_cov(itr, str(arm) + '.best')

      # update lists and counters
      self.pulls.append(arm)
      if gcov == 0:
        self.arm_satcnt[arm] += 1
      else:
        self.arm_satcnt[arm] = 0
      self.arm_pulls[arm] += 1

      return reward

    def saturate(self, arm):
      if self.arm_satcnt[arm] == self.satw:
        print('Resetting saturated arm: ' + str(arm))
        self.arm_satcnt[arm] = 0
        self.arm_pulls[arm] = 0
        self.arm_probs[arm] = np.random.dirichlet(np.ones(args.knobs),size=1)[0]
        self.weights[arm] = (np.sum(self.weights) - self.weights[arm]) / (self.arms - 1)
        fuzz.rm_dir(str(arm) + '.best')

    def run(self, iterations):
        """
        Run the EXP3 simulation.
        """
        fuzz.clean_sim()
        with open('mab.raw', 'w') as fraw, open('mab.align', 'w') as falign:
          for itr in range(iterations):
              chosen_arm = self.select_arm()
              chosen_probs = self.arm_probs[chosen_arm]
              reward = self.step(itr, chosen_arm, chosen_probs)

              self.update(chosen_arm, reward)
              self.saturate(chosen_arm)

              craw = int(fuzz.get_craw('gbest'))
              calign = int(fuzz.get_calign('gbest'))
              fraw.write(str(craw) + '\n')
              falign.write(str(calign) + '\n')
              fraw.flush()
              falign.flush()

        print(craw)
        print(calign)

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="MAB Fuzzing")

    # Add arguments
    parser.add_argument("--iterations", type=int, required=True, help="Number of iterations")
    parser.add_argument("--arms", type=int, required=True, help="Number of arms")
    parser.add_argument("--gamma", type=float, required=True, help="Exploration parameter (0 < gamma <= 1)")
    parser.add_argument("--knobs", type=int, required=True, help="Number of Cascade knobs")
    parser.add_argument("--alpha", type=float, required=True, help="Local reward parameter (0 < alpha <= 1)")
    parser.add_argument("--satw", type=int, required=True, help="Arm saturation window length")

    # Parse arguments
    args = parser.parse_args()

    arm_probs = np.random.dirichlet(np.ones(args.knobs),size=args.arms)
    pprint.pp(arm_probs)

    exp3 = EXP3(arms=args.arms, arm_probs=arm_probs, gamma=args.gamma, alpha=args.alpha, satw=args.satw)
    exp3.run(iterations=args.iterations)
