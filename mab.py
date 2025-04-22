import numpy as np
import sys
import os
import argparse
import pprint
import itertools

import fuzz

class EXP3:
    def __init__(self, arms, arm_probs, gamma, alpha, window):
        """
        Initialize the EXP3 algorithm.
        """
        self.arms = arms
        self.arm_probs = arm_probs
        self.gamma = gamma
        self.alpha = alpha
        self.window = window
        self.weights = [[1 for _ in range(window)] for _ in range(arms)]

        self.arm_pulls = [0] * self.arms
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
        prod_weights = np.prod(self.weights, axis=1)
        total_weight = np.sum(prod_weights)
        probabilities = (1 - self.gamma) * (prod_weights / total_weight) + (self.gamma / self.arms)
        return probabilities

    def update(self, chosen_arm, reward):
        """
        Update the weights of the chosen arm based on the received reward.
        """
        probabilities = self.get_probabilities()
        estimated_reward = reward / probabilities[chosen_arm]
        self.weights[chosen_arm].pop(0)
        self.weights[chosen_arm].append(np.exp(self.gamma * estimated_reward / self.arms))

    def step(self, itr, arm, probs):
      print('------------------------')
      print('Arm probabilities: ', *self.get_probabilities())
      print('Arm weights: ', *np.prod(self.weights, axis=1))
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
      reward = (1 - np.exp(-0.05 * reward)) / (1 + np.exp(-0.05 * reward))
      print('gcov: ' + str(gcov))
      print('lcov: ' + str(lcov))
      print('reward: ' + str(reward))

      # update best coverage
      fuzz.update_cov(itr, 'gbest')
      fuzz.update_cov(itr, str(arm) + '.best')

      # update lists and counters
      self.pulls.append(arm)
      self.arm_pulls[arm] += 1

      return reward

    def run(self, iterations):
        """
        Run the EXP3 simulation.
        """
        fuzz.clean_sim()
        with open('mab.raw', 'w') as fraw, open('mab.align', 'w') as falign, open('mab.arms', 'w') as farm:
          for itr in range(iterations):
              chosen_arm = self.select_arm()
              chosen_probs = self.arm_probs[chosen_arm]
              reward = self.step(itr, chosen_arm, chosen_probs)

              self.update(chosen_arm, reward)

              craw = int(fuzz.get_craw('gbest'))
              calign = int(fuzz.get_calign('gbest'))
              fraw.write(str(craw) + '\n')
              falign.write(str(calign) + '\n')
              farm.write(' '.join(map(str, self.get_probabilities())) + '\n')
              fraw.flush()
              falign.flush()
              farm.flush()

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
    parser.add_argument("--window", type=int, required=True, help="Observation window")

    # Parse arguments
    args = parser.parse_args()

    np.random.seed(0)
    max_knobs = []
    arm_probs = []
    while len(arm_probs) < args.arms:
      probs = np.random.dirichlet(0.1 * np.ones(args.knobs),size=1)[0]
      max_knob = np.argmax(probs)
      if (max_knob == len(max_knobs)) or (len(max_knobs) >= args.knobs):
        max_knobs.append(max_knob)
        arm_probs.append(probs)

    print(max_knobs)
    pprint.pp(arm_probs)

    exp3 = EXP3(arms=args.arms, arm_probs=arm_probs, gamma=args.gamma, alpha=args.alpha, window=args.window)
    exp3.run(iterations=args.iterations)
