from yahtzee import YahtzeeGame
from yahtzee_env import YahtzeeEnv
from agents import human, random_agent
import argparse
import pandas as pd

AGENTS = {'human': human.Human, 'random' : random_agent.RandomAgent}

def main(args):
	try:
		agents = [AGENTS[args.agent]() for _ in range(args.num_players)]
	except KeyError:
		print("Agent \"" + args.agent + "\" is invalid...")
		print("Valid agents are", ','.join(list(AGENTS.keys())))
		return
	env = YahtzeeEnv(num_players=args.num_players)

	scores = [[] for _ in range(args.num_players)]
	for i in range(args.n):
		state = env.reset()
		if (args.render):
			env.render()
		done = False
		while (not done):
			turn = env.turn
			action = agents[turn].act(state[turn])
			state, reward, done, _ = env.step(action)
			if (not done and args.render):
				env.render()
		for i in range(args.num_players):
			if (args.render):
				print("player", i)
				print(state[i])
			game_i = dict(state[i].sheet.as_list())
			game_i["win"] = env.winner() == i
			scores[i].append(game_i)

	if (args.n > 1 or not args.render):
		for i in range(args.num_players):
			print(pd.DataFrame(scores[i]).mean())

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-num_players', '-np', dest="num_players", type=int, default=1)
	parser.add_argument('-agent', '-a', dest="agent", default="human")
	parser.add_argument('-num_games', '-n', dest="n", type=int, default="1")
	parser.add_argument('-render', '-r', dest="render", action="store_true")
	args = parser.parse_args()
	if (args.agent == "human"):
		args.render = True
	main(args)