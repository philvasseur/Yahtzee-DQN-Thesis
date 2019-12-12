from yahtzee import YahtzeeScoresheet, YahtzeeRoll
import numpy as np
import random, sys
from config import *

def progressBar(value, endvalue, bar_length=100):
    sys.stdout.write("\rGame {0} / {1}".format(value, endvalue))
    sys.stdout.flush()

def convert_nn_input(sheet, roll, rerolls):
	conv_data = [int(sheet.is_marked(i)) for i in range(12)]
	if sheet.scores[YahtzeeScoresheet.YAHTZEE] is not None:
		if sheet.scores[YahtzeeScoresheet.YAHTZEE] > 0:
			conv_data += [0, 1]
		else:
			conv_data += [1, 0]
	else:
		conv_data += [0, 0]
	up_val = min(sheet._upper_total, 63)  
	conv_data.append(round(up_val/63, 5))

	die_counts = roll.dice.freq
	die_counts = [c / 5 for c in die_counts]

	# reroll_count = [0, 0, 0]
	# reroll_count[rerolls] += 1
	reroll_count = [rerolls / 2]

	conv_data = conv_data + die_counts + reroll_count
	return np.array(conv_data)

def best_cat(sheet, roll, cats, throw_away_cats):
	valid_cats = [c for c in cats if not sheet.is_marked(c)]
	if (valid_cats):
		cat_and_score = [(cat, sheet.score(cat, roll)) for cat in valid_cats]
		best_cat = max(cat_and_score, key=lambda p: p[1])
		if (best_cat[1] > 0): return best_cat[0]
		# All valid categories give scores of 0, have to throw away 1
		for c in throw_away_cats:
			if c in valid_cats:
				return c
	return None

def meta_action_to_cat(sheet, roll, output_index):
	yahtzee_cat = None
	if output_index >= 0 and output_index < N_KIND_OUTPUT_INDEX:
		yahtzee_cat = None if sheet.is_marked(output_index) else output_index
	elif output_index == N_KIND_OUTPUT_INDEX:
		cats = [YahtzeeScoresheet.YAHTZEE, YahtzeeScoresheet.FOUR_KIND, YahtzeeScoresheet.THREE_KIND]
		throw_away_cats = [YahtzeeScoresheet.FOUR_KIND, YahtzeeScoresheet.YAHTZEE, YahtzeeScoresheet.THREE_KIND]
		yahtzee_cat = best_cat(sheet, roll, cats, throw_away_cats)
	elif output_index == FH_OUTPUT_INDEX:
		yahtzee_cat = None if sheet.is_marked(YahtzeeScoresheet.FULL_HOUSE) else YahtzeeScoresheet.FULL_HOUSE
	elif output_index == STRAIGHT_OUTPUT_INDEX:
		cats = [YahtzeeScoresheet.LARGE_STRAIGHT, YahtzeeScoresheet.SMALL_STRAIGHT]
		yahtzee_cat = best_cat(sheet, roll, cats, cats)
	elif output_index == CHANCE_OUTPUT_INDEX:
		yahtzee_cat = None if sheet.is_marked(YahtzeeScoresheet.CHANCE) else YahtzeeScoresheet.CHANCE
	else:
		raise ValueError("Invalid output category " + str(output_index))

	if (yahtzee_cat == None):
		yahtzee_cat = random.choice([c for c in range(13) if not sheet.is_marked(c)])
	return yahtzee_cat

def meta_action_to_roll(sheet, roll, rerolls, output_index):
	if output_index >= 0 and output_index < N_KIND_OUTPUT_INDEX:
		return roll.select_all([output_index + 1])
	elif output_index == N_KIND_OUTPUT_INDEX:
		return roll.select_for_n_kind(sheet, rerolls)
	elif output_index == FH_OUTPUT_INDEX:
		return roll.select_for_full_house()
	elif output_index == STRAIGHT_OUTPUT_INDEX:
		return roll.select_for_straight(sheet)
	elif output_index == CHANCE_OUTPUT_INDEX:
		return roll.select_for_chance(rerolls)
	else:
		raise ValueError("Invalid meta_action index " + str(output_index))

def convert_meta_action(sheet, roll, rerolls, meta_action):
	if (rerolls == 0):
		return meta_action_to_cat(sheet, roll, meta_action)
	return meta_action_to_roll(sheet, roll, rerolls, meta_action)
