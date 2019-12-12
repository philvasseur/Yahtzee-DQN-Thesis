from yahtzee import YahtzeeScoresheet
import random

class RandomAgent:
	def __init__(self):
		pass

	def act(self, game):
		if (game.rerolls > 0):
			return self.choose_dice(game.sheet, game.roll, game.rerolls)
		else:
			return self.choose_category(game.sheet, game.roll)

	def __init__(self):
		self.cat = None

		# what we hope to score in each category
		self.goals = [3, 6, 9, 12, 15, 18, 20, 10, 15, 20, 15, 25, 10]

	def choose_dice(self, sheet, roll, rerolls):
		# randomly choose an unsed category at the beginning of each turn
		if rerolls == 2:
			self.pick_random_category(sheet)

		# select dice according to which category we chose to try for
		# at the beginning of the turn
		if self.cat >= 0 and self.cat < YahtzeeScoresheet.THREE_KIND:
			return roll.select_all([self.cat + 1])
		elif self.cat in [YahtzeeScoresheet.THREE_KIND, YahtzeeScoresheet.FOUR_KIND, YahtzeeScoresheet.YAHTZEE]:
			return roll.select_for_n_kind(sheet, rerolls)
		elif self.cat == YahtzeeScoresheet.FULL_HOUSE:
			return roll.select_for_full_house()
		elif self.cat == YahtzeeScoresheet.CHANCE:
			return roll.select_for_chance(rerolls)
		else:
			return roll.select_for_straight(sheet)

		
	def choose_category(self, sheet, roll):
		''' Returns the free category that minimizes regret.
		'''
		# for each category, compute the difference between what we
		# would score in that category and what we hoped to score
		regrets = [(cat, self.goals[cat] - sheet.score(cat, roll))  for cat in range(0, 13) if not sheet.is_marked(cat)]

		# greedily choose the category that minimizes that difference
		return min(regrets, key=lambda x:x[1])[0]
		

	def pick_random_category(self, sheet):
		''' Randomly uniformly chooses an unsed category on the given
			scoresheet.

			sheet -- a YahtzeeScoresheet
		'''
		self.cat = None
		count = 0
		for c in range(13):
			if not sheet.is_marked(c):
				count += 1
				if random.random() < 1.0 / count:
					self.cat = c

