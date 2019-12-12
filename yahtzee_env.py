import gym
from gym import error, spaces, utils
from gym.utils import seeding
from yahtzee import YahtzeeGame, YahtzeeScoresheet, YahtzeeRoll
from util import convert_nn_input, convert_meta_action
import numpy as np

class YahtzeeEnv(gym.Env):
	metadata = {'render.modes': ['human']}

	def __init__(self, num_players=1):
		self.num_players = num_players
		self.turn = 0
		self.reset()

	def step(self, meta_action):
		game = self.games[self.turn]
		if (game.rerolls == 0):
			self.turn = (self.turn + 1) % self.num_players
		if (game.game_over()):
			return [game, 0, True, {}]
		action = convert_meta_action(game.sheet, game.roll, game.rerolls, meta_action)
		prev_score = game.total_score()
		game.make_move(action)
		reward = game.total_score() - prev_score
		return [self.get_state(), reward, np.all([g.game_over() for g in self.games]), {}]
		
	def reset(self):
		self.games = [YahtzeeGame() for _ in range(self.num_players)]
		return self.get_state()

	def render(self):
		print("player", self.turn)
		print(self.games[self.turn])
		print()

	def winner(self):
		assert(np.all([g.game_over() for g in self.games]))
		return np.argmax([g.total_score() for g in self.games])

	def get_state(self):
		# return self.games
		# score_diff = [np.array([self.games[self.turn].total_score() - g.total_score() for g in self.games if g != self.games[self.turn]])]
		current_game = [convert_nn_input(self.games[self.turn].sheet, self.games[self.turn].roll, self.games[self.turn].rerolls)]
		other_games = [convert_nn_input(g.sheet, g.roll, g.rerolls) for g in self.games if g != self.games[self.turn]]
		return np.concatenate(current_game + other_games)
