from multiset import Multiset
import random
import itertools

class DiceRoll:
    ''' The outcome of rolling a collection of indistinguishable fair dice.
        Rolls are immutable so they can be used as dictionary keys.
        Includes methods for creating new rolls by adding randomly rolled
        dice to an existing roll, and creating subrolls by selecting
        certain dice from a roll.
    '''

    def __init__(self, pips, sides):
        ''' Creates a roll with dice showing the numbers in the given iterable
            and the given number of sides.

            pips -- an iterable over integers between 1 and sides (inclusive)
            sides -- a positive integer
        '''
        self._dice = Multiset(sides)
        self._hash = None
        for n in pips:
            self._dice.add(n - 1)


    @staticmethod
    def roll(count, sides):
        ''' Creates and returns a random roll of the given number of dice with
            the given number of sides.

            count -- a nonnegative integer
            sides -- a positive integer
        '''
        result = DiceRoll([], sides)
        result._dice.add_random(count)
        return result


    @staticmethod
    def parse(s, sides):
        ''' Returns a roll containing dice showing the numbers corresponding
            to the digits in the given string.

            s -- a string containing digits in the range 1 through sides
            sided -- a positive integer
        '''
        if sides <= 0:
            raise ValueError("number of sides must be positive: {0}".format(sides))
        pips = []
        for digit in s:
            if not digit.isdigit():
                raise ValueError("invalid digit {0} in {1}".format(digit, s))
            num = int(digit)
            if num < 1 or num > sides:
                raise ValueError("invalid digit {0} in {1} for {2} sides".format(digit, s, sides))
            pips.append(num)
        return DiceRoll(pips, sides)


    def size(self):
        ''' Returns the number of dice in this roll.
        '''
        return self._dice.size()


    def sides(self):
        ''' Returns the number of sides on the dice in this roll.
        '''
        return self._dice.maximum()


    def min_number(self):
        ''' Returns the minimum number showing in this roll.
            If there are no dice in this roll then the
            value returned is larger than the number of sides.
        '''
        return self._dice.min_element() + 1


    def max_number(self):
        ''' Returns the maximum number showing in this roll.
            If there are no dice in this roll then the
            value returned is zero or less.
        '''
        return self._dice.max_element() + 1

    
    def copy(self):
        ''' Returns a copy of this roll.
        '''
        return DiceRoll(self.as_list(), self.sides())

            
    def reroll(self, total):
        ''' Creates and returns a roll containing dice showing the same numbers
            as in this roll, plus additional randomly rolled dice so the total
            dice is as given.

            total -- an integer greater than or equal to the number of dice
                     in this roll
        '''
        if total < self.size():
            raise ValueError("can't reroll to fewer dice: {0} < {1}".format(total, self.size()))
        result = self.copy()
        result._dice.add_random(total - self.size())
        return result


    def add_one(self, num):
        ''' Creates and returns a roll containing the same dice as this one
            plus one showing the given number.

            num -- an integer between 1 and the number of sides on the dice
                   in this roll (inclusive)
        '''
        if num < 1 or num > self.sides():
            raise ValueError("number out of range for {1}-sided dice: {0}".format(num, self.sides()))
        result = self.copy()
        result._dice.add(num - 1)
        return result


    def subroll(self, other):
        ''' Determines if this roll is a subset of the given roll.  One roll is
            a subset of another if the dice in the two rolls have the same number
            of sides and there is a 1-1 mapping from the first roll to dice
            in the second showing the same number.
        
            other -- a Yahtzee roll
        '''
        return self.sides() == other.sides() and self._dice.subset(other._dice)


    def count(self, num):
        ''' Determines how mnay dice are showing the given number.
        
            num -- an integer
        '''
        return self._dice.count(num - 1)


    def total(self):
        ''' Returns the total showing on the dice.
        '''
        # total in the dice + 1 for each to account for 0...5 vs 1...6
        return self._dice.total() + self._dice.size()


    def all_subrolls(self):
        ''' Returns a list containing all the subrolls of this roll.
        '''
        result = []

        # for each possible number, compute the range of how may dice
        # showing that number we can keep.  For example, for four-sided
        # dice [1, 2, 2, 4] we want [0..1, 0..2, 0, 0..1]
        options = []
        for i in range(self.sides()):
            options.append(range(self.count(i + 1) + 1))

        # for each possible combination of how many of each number,
        # create the corresponding roll
        for counts in itertools.product(*options):
            s = []
            for i in range(self.sides()):
                # add counts[i] dice showing i + 1
                for k in range(counts[i]):
                    s.append(i + 1)
            result.append(DiceRoll(s, self.sides()))

        return result


    def as_list(self):
        ''' Returns a list of the numbers showing in this roll.  The
            list returned will be sorted from lowest to highest number showing.
        '''
        return [x + 1 for x in self._dice.as_list()]


    def as_tuple(self):
        ''' Returns a tuple of the numbers showing in this roll.  The tuple
            returned will be sorted from lowest to highest number showing.
        '''
        return tuple([x + 1 for x in self._dice.as_list()])


    def select_all(self, nums, maximum=None):
        ''' Returns the subroll of this roll that contains all occurrences
            of the given numbers up to the given maximum of each.  If the
            maximum is None then there is no limit.

            nums -- a list of integers betwen 1 and the number of sides
                    on the dice in this roll
            maximum -- an integer, or None
        '''
        keep = []
        # for each number in the list, add as many of that number as are
        # in the roll, up to the given maximum
        for n in nums:
            if n < 1 or n > self.sides():
                raise ValueError("value out of range in {0}".format(nums))
            for i in range(self.count(n) if maximum is None else min(maximum, self.count(n))):
                keep.append(n)
        return DiceRoll(keep, self.sides())


    def select_one(self, nums):
        ''' Returns the subroll of this roll that contains one occurrence
            of each of the given numbers that are also in this roll.

            nums -- a list of integers betwen 1 and the number of sides on the
                    dice in this roll
        '''
        keep = []
        # for each number in the list, add one of that number if the roll
        # contains at least one
        for n in nums:
            if n < 1 or n > self.sides():
                raise ValueError("value out of range in {0}".format(nums))
            if self.count(n) > 0:
                keep.append(n)
        return DiceRoll(keep, self.sides())


    def longest_runs(self):
        ''' Returns a list of all the longest consecutive runs in this
            roll.  For example, if this roll is [1 2 4 4 5] then the
            list returned is [[1, 2], [4, 5]].
        '''
        runs = []
        longest = 0
        curr_len = 0
        for i in range(1, self.sides() + 1):
            if self.count(i) > 0:
                curr_len += 1
                if curr_len == longest:
                    runs.append(list(range(i - curr_len + 1, i + 1)))
                elif curr_len > longest:
                    runs = [list(range(i - curr_len + 1, i + 1))]
                    longest = curr_len
            else:
                curr_len = 0
        return runs
        
        
    def __str__(self):
        ''' Returns a string representation of this roll.
        '''
        return str(self.as_list())


    def __repr__(self):
        return self.__str__()


    def __hash__(self):
        if self._hash is None:
            self._hash = (self.sides(), self.as_tuple()).__hash__()
        return self._hash

        
    def __eq__(self, other):
        ''' Determines if this roll is equal to the given other roll.
            Two rolls are equal if their dice show the same numbers
            and have the same number of sides.
        '''
        return self.sides() == other.sides() and self._dice == other._dice


    def __iter__(self):
        ''' Returns an iterator over the numbers showing in this roll.
        '''
        # delegate to the tuple representation
        return self.as_tuple().__iter__()
