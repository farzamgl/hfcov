import numpy as np
import sys
import os
import argparse
import pprint

#current = os.path.dirname(os.path.realpath(__file__))
#parent = os.path.dirname(current)
#sys.path.append(parent)

import fuzz

class EXP3:
    def __init__(self, arms, gamma, alpha):
        """
        Initialize the EXP3 algorithm.
        """
        self.arms = arms
        self.gamma = gamma
        self.alpha = alpha
        self.weights = np.ones(arms)  # Initialize weights for each arm

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

        :param chosen_arm: The index of the chosen arm.
        :param reward: The reward received (normalized between 0 and 1).
        """
        probabilities = self.get_probabilities()
        estimated_reward = reward / probabilities[chosen_arm]
        self.weights[chosen_arm] *= np.exp(self.gamma * estimated_reward / self.arms)

    def step(self, itr, arm, probs):
      # create an nbf with input probs
      fuzz.cascade_run(itr, probs.tolist())

      # run verilator sim and gather coverage files
      fuzz.run_sim(itr)

      # calculate reward based on comparing with previous best coverage
      greward = fuzz.reward_cov(itr, 'gbest')
      lreward = fuzz.reward_cov(itr, str(arm) + '.best')
      reward = (self.alpha * lreward) + ((1 - self.alpha) * greward)

      # update best coverage
      fuzz.update_cov(itr, 'gbest')
      fuzz.update_cov(itr, str(arm) + '.best')

      return reward

    def run(self, arm_probs, iterations):
        """
        Run the EXP3 simulation.
        """
        fuzz.clean_sim()
        for itr in range(iterations):
            chosen_arm = self.select_arm()
            chosen_probs = arm_probs[chosen_arm]
            reward = self.step(itr, chosen_arm, chosen_probs)
            # TODO: normalize reward
            self.update(chosen_arm, reward)

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="MAB Fuzzing")

    # Add arguments
    parser.add_argument("--iterations", type=int, required=True, help="Number of iterations")
    parser.add_argument("--arms", type=int, required=True, help="Number of arms")
    parser.add_argument("--gamma", type=float, required=True, help="Exploration parameter (0 < gamma <= 1)")
    parser.add_argument("--knobs", type=int, required=True, help="Number of Cascade knobs")
    parser.add_argument("--alpha", type=float, required=True, help="Local reward parameter (0 < alpha <= 1)")

    # Parse arguments
    args = parser.parse_args()

    arm_probs = np.random.dirichlet(np.ones(args.knobs),size=args.arms)
    pprint.pp(arm_probs)

    exp3 = EXP3(arms=args.arms, gamma=args.gamma, alpha=args.alpha)
    exp3.run(arm_probs=arm_probs, iterations=args.iterations)
