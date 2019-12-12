# A solver for various forms of solitaire Yahtzee.  The game rules are
# defined by an game rules object that provides methods for
# implementing scoring rules and for representing positions (all of
# the information about the current state of the game that a player
# would like to see), and equivalence classes of anchors (sets of
# start-of-turn positions [anchors] with the same optimal strategy
# throughout their components) as tuples (for ease of interpretation)
# and integer indices (for efficiency of lookup), and methods for
# converting between those methods of representation.

import itertools
import math
import random
import sys
import argparse
from roll import DiceRoll

class YahtzeeFlags:
    UNUSED = 0
    ZERO = 1
    NONZERO = 2


def null_log(pos):
    pass


def random_sample(game, fraction):
    def log(pos):
        if (random.randint(1, fraction) == 1):
            print(game.position_to_string(pos))
    return log


def solve(game, dice_action_filter, category_action_filter, values=None):
    """ Solves for the optimal strategy for the solitaire game defined
        by the given object, restricted to actions allowed by the
        given filter.

        game -- a solitaire Yahtzee game
        action_filter -- a function that, given a game, an anchor, a roll,
        and the number of rolls left, returns a list of the possible
        combinations of dice to keep
        returns a list of the possible combinations of dice to keep
    """
    # make initial list of position values
    if values is None:
        values = [float("NaN")] * (game.maximum_index() + 1)

    # iterate backwards through all tuples representing equivalence classes
    # of positions
    max_tuple = game.maximum_tuple()
    ranges = [range(x, -1, -1) for x in max_tuple]
    for anchor_tuple in itertools.product(*ranges):
        # convert tuple representation of current class to integer index
        anchor_index = game.tuple_to_index(anchor_tuple)

        if not math.isnan(values[anchor_index]):
            continue
        
        # check that current class is actually possible
        if anchor_index is not None:
            # check whether positions in current class are terminal
            if game.is_terminal_anchor(anchor_tuple):
                values[anchor_index] = game.terminal_value(anchor_tuple)
            else:
                # compute value of anchor by working through induced
                # component from successor anchors
                values[anchor_index] = solve_component(anchor_tuple, game, dice_action_filter, category_action_filter, values)[(game.rerolls() + 1, DiceRoll([], game.num_sides()))]
            print(anchor_tuple, values[anchor_index])
    return values[0]


def solve_component(anchor_tuple, game, dice_action_filter, category_action_filter, values):
    """ Solves for the optimal solitaire strategy across the component
        anchored by the given position in the given game, allowing keep
        actions determined by the given filter, and given the values of
        all successor anchors in the given list.
 
        anchor_tuple -- an anchor in the game, represented as a tuple
        game -- a solitaire Yahtzee game
        dice_action_filter -- a function that, given a game, an anchor, a roll,
        and the number of rolls left, returns a list of possible combinations
        of dice to keep
        category_action_filter -- a function that, given an game, and anchor,
        and a roll, returns a list of possible categories to score in
        values -- a list containing position values for all anchors that
        are immediate successors of anchor_tuple
    """
    # make an empty map from positions in the component to their values
    component_values = {}

    # iterate through all positions in the component from no rerolls left
    # to the initial roll; positions are represented by tuples (roll, rerolls)
    # where roll is the current state of the dice and rerolls is the number
    # of rolls left
    for position in itertools.chain(itertools.product([0], game.complete_rolls()), itertools.product(range(1, game.rerolls() + 1), itertools.chain(game.partial_rolls(), game.complete_rolls())), itertools.product([game.rerolls() + 1], game.partial_rolls())):
        rerolls, roll = position
        if rerolls == 0:
            # end of turn; maximize over unused categories
            component_values[position] =  max(values[game.tuple_to_index(x[0])] + x[1] for x in [game.update(anchor_tuple, roll, cat) for cat in category_action_filter(game, anchor_tuple, roll)])
        elif roll.size() == game.num_dice():
            # roll is complete; maximize over choices of dice to keep
            component_values[position] = max(component_values[(rerolls - 1 if keep.size() == game.num_dice() else rerolls, keep)] for keep in dice_action_filter(game, anchor_tuple, roll, rerolls))
        else:
            # roll is partial; take average over all single dice that
            # could be added
            component_values[position] = sum(component_values[(rerolls - 1 if roll.size() == game.num_dice() - 1 else rerolls, roll.add_one(x))] for x in range(1, game.num_sides() + 1)) / game.num_sides()

    return component_values


def upper(num, update):
    def score(anchor_tuple, roll, cat):
        points = {cat: roll.count(num) * num}
        return (update(anchor_tuple, roll, cat), points)
    return score


def upper_bonus(ub_level, ub_value, ub_slot):
    def make_category(inner):
        def score(anchor_tuple, roll, cat):
            succ_tuple, points = inner(anchor_tuple, roll, cat)
            _, upper, _ = anchor_tuple
            yahtzee, _, used = succ_tuple
            if upper < ub_level and upper + points[cat] >= ub_level:
                points[ub_slot] = ub_value
            return ((yahtzee, min(upper + points[cat], ub_level), used), points)
        return score
    return make_category


def mark_used(anchor_tuple, roll, cat):
    yahtzee, upper, used = anchor_tuple
    return (yahtzee, upper, used + (1 << cat))


def mark_yahtzee(anchor_tuple, roll, cat):
    _, upper, used = anchor_tuple
    return (YahtzeeFlags.NONZERO if is_yahtzee(roll) else YahtzeeFlags.ZERO, upper, used)


def free_joker_disallowed(upper_cats, inner, update):
    # free joker allows regular scoring in other categories
    def score(anchor_tuple, roll, cat):
        return inner(anchor_tuple, roll, cat)
    return score


def free_joker_allowed(upper_cats, value, inner, update):
    def score(anchor_tuple, roll, cat):
        yahtzee, upper, used = anchor_tuple
        if yahtzee == YahtzeeFlags.UNUSED or not is_yahtzee(roll):
            # yahtzee not used yet or roll is not a yahtzee
            return inner(anchor_tuple, roll, cat)
        else:
            # yahtzee has been used and roll is a yahtzee; joker in this
            # category if corresponding upper is used
            if (used & (1 << upper_cats[roll.min_number() - 1])) != 0:
                return (update(anchor_tuple, roll, cat), {cat: value})
            else:
                return (update(anchor_tuple, roll, cat), {cat: 0})
    return score


def is_n_kind(roll, count):
    return sum(1 if roll.count(x) >= count else 0 for x in roll) > 0


def n_kind(count, scoring, update):
    def score(anchor_tuple, roll, cat):
        if is_n_kind(roll, count):
            return (update(anchor_tuple, roll, cat), {cat: scoring(roll)})
        else:
            return (update(anchor_tuple, roll, cat), {cat: 0})
    return score


def is_straight(roll, length):
    if length == 1:
        return roll.size() >= 1
    counts = [roll.count(x) for x in range(roll.min_number(), roll.max_number() + 1)]
    if len(counts) < length:
        return False
    run = 1
    for i in range(1, len(counts)):
        if counts[i] == 0:
            run = 0
        else:
            run += 1
            if run == length:
                return True
    return False


def straight(length, value, update):
    def score(anchor_tuple, roll, cat):
        return (update(anchor_tuple, roll, cat), {cat: value if is_straight(roll, length) else 0})
    return score


def is_full_house(roll):
    min_count = roll.count(roll.min_number())
    max_count = roll.count(roll.max_number())
    return min_count + max_count == roll.size() and min_count > 1 and max_count > 1


def full_house(value, update):
    def score(anchor_tuple, roll, cat):
        return(update(anchor_tuple, roll, cat), {cat: value if is_full_house(roll) else 0})
    return score

        
def is_yahtzee(roll):
    return roll.count(roll.min_number()) == roll.size()


def yahtzee_bonus(value, inner, yb_slot):
    def score(anchor_tuple, roll, cat):
        yahtzee, _, _ = anchor_tuple
        succ, points = inner(anchor_tuple, roll, cat)
        if yahtzee == YahtzeeFlags.NONZERO and is_yahtzee(roll):
            points[yb_slot] = value
        return (succ, points) 
    return score


class StandardYahtzee:
    def __init__(self, ub_level, ub_value, fh_value, ss_value, ls_value, y_value, y_bonus):
        self._params = (ub_level, ub_value, fh_value, ss_value, ls_value, y_value, y_bonus)

        self.upper_bonus_level = ub_level
        self.upper_total_bits = int(math.log2(ub_level)) + 1

        ub = upper_bonus(ub_level, ub_value, 13)
        joker_allowed = free_joker_allowed
        joker_disallowed = free_joker_disallowed
        self.categories = [yahtzee_bonus(y_bonus, inner, 14)
                           for inner in [ub(upper(1, mark_used)),
                                         ub(upper(2, mark_used)),
                                         ub(upper(3, mark_used)),
                                         ub(upper(4, mark_used)),
                                         ub(upper(5, mark_used)),
                                         ub(upper(6, mark_used)),
                                         joker_disallowed(list(range(6)), n_kind(3, sum, mark_used), mark_used),
                                         joker_disallowed(list(range(6)), n_kind(4, sum, mark_used), mark_used),
                                         joker_allowed(list(range(6)), fh_value, full_house(fh_value, mark_used), mark_used),
                                         joker_allowed(list(range(6)), ss_value, straight(4, ss_value, mark_used), mark_used),
                                         joker_allowed(list(range(6)), ls_value, straight(5, ls_value, mark_used), mark_used),
                                         joker_disallowed(list(range(6)), n_kind(1, sum, mark_used), mark_used),
                                         n_kind(5, lambda roll: y_value if is_yahtzee(roll) else 0, mark_yahtzee)]]
        self._abbrevs = ['1', '2', '3', '4', '5', '6', '3K', '4K', 'FH', 'SS', 'LS', 'C', 'Y']
        self._cat_to_index = {abbrev: i for i, abbrev in enumerate(self._abbrevs)}

        self._scoresheet_display = [("Aces", lambda sheet: sheet[0]),
                                    ("Deuces", lambda sheet: sheet[1]),
                                    ("Treys", lambda sheet: sheet[2]),
                                    ("Fours", lambda sheet: sheet[3]),
                                    ("Fives", lambda sheet: sheet[4]),
                                    ("Sixes", lambda sheet: sheet[5]),
                                    ("UPPER BONUS", lambda sheet: sheet[13]),
                                    ("UPPER TOTAL", lambda sheet: sum(0 if sheet[i] is None else sheet[i] for i in range(6)) + (0 if sheet[13] is None else sheet[13])),
                                    None,
                                    ("Three of a Kind", lambda sheet: sheet[6]),
                                    ("Four of a Kind", lambda sheet: sheet[7]),
                                    ("Full House", lambda sheet: sheet[8]),
                                    ("Small Straight", lambda sheet: sheet[9]),
                                    ("Large Straight", lambda sheet: sheet[10]),
                                    ("Chance", lambda sheet: sheet[11]),
                                    ("Yahtzee", lambda sheet: sheet[12]),
                                    ("YAHTZEE BONUS", lambda sheet: sheet[14]),
                                    ("LOWER TOTAL", lambda sheet: sum(0 if sheet[i] is None else sheet[i] for i in range(6, 13)) + 0 if sheet[14] is None else sheet[14]),
                                    None,
                                    ("GRAND TOTAL", lambda sheet: sum(0 if sheet[i] is None else sheet[i] for i in range(len(sheet))))]

        # precompute lists of complete and partial rolls for efficiency
        # (note we return these lists w/o a way to prevent users from
        # modifying the -- why no frozenlist?  are we to make tuples instead
        # [seems wrong to me -- to me, tuples and lists, although structurally
        # similar, usually represent different kinds of things -- tuples
        # represent objects that can be described as a combination of values;
        # lists are lists of separate, possibly unrelated, objects]
        self.complete_roll_list = [DiceRoll(x, self.num_sides()) for x in itertools.combinations_with_replacement(range(1, self.num_sides() + 1), self.num_dice())]
        self.partial_roll_list = [DiceRoll(x, self.num_sides()) for x in itertools.chain(*[itertools.combinations_with_replacement(range(1, self.num_sides() + 1), x) for x in range(self.num_dice() - 1, -1, -1)])]

        self.subroll_list = {}
        for roll in self.complete_roll_list:
            self.subroll_list[roll] = roll.all_subrolls()
            
        self.unused_category_list = {(yahtzee, used):([self.find_category("Y")] if yahtzee == YahtzeeFlags.UNUSED else []) + [x for x in range(len(self.categories) - 1) if (used & (1 << x)) == 0] for yahtzee in range(YahtzeeFlags.NONZERO + 1) for used in range(1 << (len(self.categories) - 1))}

        
    def __hash__(self):
        return self._params.__hash__()


    def __eq__(self, other):
        return self._params == other._params


    def maximum_index(self):
        # 3 for yahtzee, 2 for other categories, 
        return 3 * 2**(len(self.categories) - 1 + self.upper_total_bits) - 1


    def maximum_tuple(self):
        return (YahtzeeFlags.NONZERO, self.upper_bonus_level, 2**(len(self.categories) - 1) - 1)


    def load_values(self, fname):
        values = [float("NaN")] * (self.maximum_index() + 1)

        # for debugging: file should contain values in form like
        # (1, 63, 4094) 2.10
        # and solver will use those values and compute only the missing ones
    
        with open(fname) as infile:
            for line in infile:
                line = line.replace("(", "")
                line = line.replace(")", ",")
                fields = line.split(",")
                values[self.tuple_to_index((int(fields[0]), int(fields[1]), int(fields[2])))] = float(fields[3])

        return values


    def initial_position(self):
        ''' Returns the initial position for this game.  The initial position is a tuple
            (anchor, scoresheet, current roll, rerolls), where scoresheet is a list of scores
            in the various categories, or None to indicate that a category hasn't been used
            yet, plus entries for the upper bonus and Yahtzee bonus.
        '''
        return ((YahtzeeFlags.UNUSED, 0, 0), [None] * (len(self.categories) + 2), DiceRoll([], self.num_sides()), self.rerolls() + 1)
    
        
    def is_terminal_position(self, pos):
        return self.is_terminal_anchor(pos[0])

        
    def play(self, policy, log):
        pos = self.initial_position()
        policy.start_turn(self, pos[0], pos[1])

        while not self.is_terminal_position(pos):
            anchor, sheet, roll, rerolls = pos
            if rerolls == 0:
                log(pos)
                cat = policy.choose_category(self, anchor, sheet, roll)
                pos = self.update_position(pos, roll, cat)
                policy.start_turn(self, pos[0], pos[1])
            elif roll.size() != self.num_dice():
                roll = roll.reroll(self.num_dice())
                policy.see_roll(roll, rerolls - 1)
                pos = (anchor, sheet, roll, rerolls - 1)
            else:
                log(pos)
                keep = policy.choose_dice(self, anchor, sheet, roll, rerolls)
                if keep == roll:
                    rerolls -= 1
                    while rerolls > 0:
                        log((anchor, sheet, roll, rerolls))
                        rerolls -= 1
                pos = (anchor, sheet, keep, rerolls)
        return self.grand_total(pos)


    def play_many(self, policy, log, count):
        return sum(self.play(policy, log) for i in range(count)) / count


    def grand_total(self, pos):
        anchor, sheet, roll, rerolls = pos
        return sum(0 if x is None else x for x in sheet)


    def scoresheet_to_string(self, sheet):
        output = []
        for slot in self._scoresheet_display:
            if slot is None:
                output.append("")
            else:
                label, lookup = slot
                value = lookup(sheet)
                if value is None:
                    output.append("     " + label)
                else:
                    output.append("{0:>4} {1}".format(value, label))
        return "\n".join(output)


    def position_to_string(self, pos):
        anchor, sheet, roll, rerolls = pos
        yahtzee, upper, used = anchor
        anchor_output = [abbrev for abbrev in self._abbrevs if self.is_used(anchor, abbrev) and abbrev != "Y"]
        if yahtzee == YahtzeeFlags.ZERO:
            anchor_output.append("Y")
        elif yahtzee == YahtzeeFlags.NONZERO:
            anchor_output.append("Y+")
        anchor_output.append("UP" +  str(upper))
        return ",".join([" ".join(anchor_output), "".join(str(n) for n in roll), str(rerolls)])


    def tuple_to_index(self, tup):
        yahtzee, upper, used = tup
        return (yahtzee << (len(self.categories) - 1 + self.upper_total_bits)) + (upper << (len(self.categories) - 1)) + used


    def parse_anchor(self, s):
        ''' Returns the tuple representation of the anchor represented by the given string.
        
            s -- a string containing category abbreviations separated by spaces, with
                 Y optionally followed by + and the upper total preceded by UP, for example
                 "1 2 4 5 6 3K 4K FH SS LS C Y+ UP58"
        '''
        yahtzee = YahtzeeFlags.UNUSED
        used = 0
        upper = 0
        cats = s.split(" ")
        for cat in cats:
            if cat[0:2] != "UP":
                if cat == "Y+":
                    yahtzee = YahtzeeFlags.NONZERO
                elif cat == "Y":
                    yahtzee = YahtzeeFlags.ZERO
                else:
                    try:
                        index = self._abbrevs.index(cat)
                    except ValueError:
                        raise ValueError("{0} is not a valid category".format(cat))
                    used = used | (1 << index)
            else:
                upper = int(cat[2:])
        return (yahtzee, upper, used)


    def is_terminal_anchor(self, tup):
        yahtzee, _, used = tup
        return yahtzee != YahtzeeFlags.UNUSED and used == (1 << (len(self.categories) - 1)) - 1


    def is_used(self, tup, abbrev):
        if abbrev in self._cat_to_index:
            return self.is_used_by_index(tup, self._cat_to_index[abbrev])
        else:
            raise ValueError("invalid category {0}".format(abbrev))


    def is_used_by_index(self, tup, index):
        yahtzee, _, used = tup
        if index >= 0 and index < self.num_categories() - 1:
            # all categories except Yahtzee encoded in used bitmap
            return (used & (1 << index)) > 0
        elif index == self.num_categories() - 1:
            # Yahtzee encoded in separate component
            return yahtzee != YahtzeeFlags.UNUSED
        else:
            raise ValueError("invalid category index {0}".format(index))


    def upper_total(self, tup):
        return tup[1]


    def yahtzee_bonus_eligible(self, tup):
        return tup[0] == YahtzeeFlags.NONZERO


    def find_category(self, abbrev):
        if abbrev in self._cat_to_index:
            return self._cat_to_index[abbrev]
        else:
            return -1


    def terminal_value(self, tup):
        return 0.0


    def rerolls(self):
        return 2


    def num_dice(self):
        return 5


    def num_sides(self):
        return 6


    def num_categories(self):
        return len(self.categories)


    def max_upper_bonus_level(self):
        return self.upper_bonus_level


    def complete_rolls(self):
        return self.complete_roll_list


    def partial_rolls(self):
        return self.partial_roll_list


    def subrolls(self, roll):
        return self.subroll_list[roll]


    def update(self, anchor_tuple, roll, cat):
        anchor, scores = self.categories[cat](anchor_tuple, roll, cat)
        return (anchor, sum(scores[cat] for cat in scores), scores)


    def update_position(self, pos, roll, cat):
        anchor, sheet, roll, rerolls = pos
        anchor, scores = self.categories[cat](anchor, roll, cat)
        for slot, score in scores.items():
            if sheet[slot] is None:
                sheet[slot] = score
            else:
                sheet[slot] += score
        return (anchor, sheet, DiceRoll([], self.num_sides()), self.rerolls() + 1)


    def score_by_slot(self, anchor_tuple, roll, cat):
        return self.update(anchor_tuple, roll, cat)[2]


    def total_score(self, anchor_tuple, roll, cat):
        return self.update(anchor_tuple, roll, cat)[1]


    def successor(self, anchor_tuple, roll, cat):
        return self.update(anchor_tuple, roll, cat)[0]


    def unused_categories(self, anchor_tuple):
        yahtzee, _, used = anchor_tuple
        return self.unused_category_list[(yahtzee, used)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve solitaire Yahtzee")
    parser.add_argument("--load", action="store", dest="load", help="load anchor values from file")
    parser.add_argument("--dir", "-d", action="store", dest="directory", default=".")
    parser.add_argument("--thresh", "-t", action="store", dest="thresh", default=63, type=int)
    args = parser.parse_args()
    
    params = (args.thresh, 35, 25, 30, 40, 50, 100)
    game = StandardYahtzee(*params)

    data_file = None
    if args.load:
        data_file = args.directory + "/" + args.load

    if data_file is not None:
        values = game.load_values(data_file)
    else:
        values = None

    solve(game,
          lambda game, anchor_tuple, roll, rerolls: game.subrolls(roll),
          lambda game, anchor_tuple, roll: game.unused_categories(anchor_tuple),
          values)
