import random
random.seed(0)
import numpy as np
np.random.seed(0)
import tensorflow as tf
tf.random.set_seed(0)
import time, sys, argparse, threading
import pandas as pd
sys.path.append("./huskarl")
import huskarl as hk
from huskarl.memory import Transition

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import matplotlib.pyplot as plt

from yahtzee_env import YahtzeeEnv
import config
from util import progressBar

class Trainer:
	def __init__(self, create_env, create_agent, num_players=1):
		self.create_env = create_env
		self.agent = create_agent()
		self.agent.save(config.NAME)
		self.other_agent = None

		self.num_players = num_players
		self.best_scores = []
		self.best_num_games = []

		if (self.num_players > 1):
			self.other_agent = create_agent()
			self.other_agent.load(config.NAME)
			self.other_agent.training = False
			

	def test(self, num_games, verbose=True):
		self.agent.training = False
		agents = [self.agent] + [self.other_agent for _ in range(self.num_players - 1)]
		env = self.create_env(self.num_players)

		scores = [[] for _ in range(self.num_players)]
		for i in range(num_games):
			state = env.reset()
			done = False
			while (not done):
				turn = env.turn
				action = agents[turn].act(state)
				state, reward, done, _ = env.step(action)

			for i in range(self.num_players):
				game_i = dict(env.games[i].sheet.as_list())
				game_i["WIN"] = env.winner() == i
				scores[i].append(game_i)

		if (verbose):
			print()
			print(pd.DataFrame(scores[0]).mean())
		self.agent.training = True
		stat = "GRAND TOTAL" if self.num_players == 1 else "WIN"
		return pd.DataFrame(scores[0]).mean().loc[stat]

	def train(self, max_steps=100000):
		self.agent.training = True
		self._train(max_steps)

	def _train(self, max_steps):
		# Keep track of rewards per episode per instance
		n_games = 0
		SARS_buffer = []

		# Create and initialize environment instances
		env = self.create_env(self.num_players)
		state = env.reset()
		agents = [self.agent] + [self.other_agent for _ in range(self.num_players - 1)]
		single_player = self.num_players == 1

		for step in range(max_steps):
			turn = env.turn
			action = agents[turn].act(state)
			next_state, reward, done, _ = env.step(action)
			if (single_player):
				self.agent.push(Transition(state, action, reward, None if done else next_state))
			elif (turn == 0):
				SARS_buffer.append(Transition(state, action, turn, None if done else next_state))

			if done:
				# reward here tells which player the SARS tuple is from
				# so if the winner played the SA pair, 1 else -1
				if (not single_player):
					reward = 1 if env.winner() == 0 else -1
					for SARS in SARS_buffer:
						win_reward = 1 if env.winner() == SARS.reward else -1
						self.agent.push(Transition(SARS.state, SARS.action, win_reward, SARS.next_state))
					SARS_buffer = []

				n_games += 1
				self.update(n_games)
				state = env.reset()
			else:
				state = next_state
			# Perform one step of the optimization
			self.agent.train(step)

		self.update(n_games, done=True)

	def update(self, n_games, done=False):
		progressBar(n_games, config.TRAIN_GAMES)
		if (n_games % config.TRAIN_EVERY_N != 0):
			return

		score_to_beat = self.best_scores[-1] if self.num_players == 1 else 0.55
		avg_reward = self.test(config.TEST_GAMES, verbose=True)
		print("\nAverage Reward:", avg_reward)
		if (avg_reward >= score_to_beat):
			score_to_beat = avg_reward
			print("Saving new best model:", config.NAME)
			self.agent.save(config.NAME)
			if (self.other_agent):
				print("Loading", config.NAME, "into other_agent")
				self.other_agent.load(config.NAME)
		else:
			print("Failed to reach threshold:", avg_reward, "<", score_to_beat)

		if (self.num_players == 1):
			self.best_scores.append(score_to_beat)
			self.best_num_games.append(n_games)

def main(args):
	print("Name:", config.NAME)
	print("Threshold:", config.THRESHOLD)
	print("Optimal Value:", config.OPTIMAL_VALUE)
	create_env = YahtzeeEnv

	input_size = config.INPUT_SIZE * args.num_players #+ (args.num_players - 1)
	model = Sequential([
		Dense(64, activation='relu', input_dim=input_size),
		Dense(32, activation='relu'),
	])

	create_agent = lambda: hk.agent.DQN(model, actions=config.OUTPUT_SIZE, enable_dueling_network=True)
	trainer = Trainer(create_env, create_agent, num_players=args.num_players)

	if (args.fname):
		agent.load(args.fname)
		print("Running initial test on preloaded model...")
		trainer.best_scores.append(trainer.test(config.TEST_GAMES))
		trainer.best_num_games.append(0)
	else:
		trainer.best_scores.append(74)
		trainer.best_num_games.append(0)
	trainer.train(config.TRAIN_GAMES * 13 * 3)
	trainer.test(config.TEST_GAMES)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-l', dest="fname")
	parser.add_argument('-np', dest="num_players", type=int, default=1)
	args = parser.parse_args()
	main(args)
