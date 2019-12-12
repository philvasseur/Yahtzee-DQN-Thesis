from util import convert_meta_action
import time

class Human:
	def act(self, game):
		mai = int(input("Meta Action Index: "))
		action = convert_meta_action(game.sheet, game.roll, game.rerolls, mai)
		print("Action Chosen:", str(action))
		print()
		return action

