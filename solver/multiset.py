import random

class Multiset:
    ''' A multiset of {0, ..., n-1}
    '''

    def __init__(self, n):
        ''' Creates an empty multiset that can contain values up to n-1.

            n -- a positive integer
        '''
        if n <= 0:
            raise ValueError("number of possible values must be positive %d" % sides)

        self._maximum = n

        # initially empty
        self._freq = [0] * n
        self._size = 0

        # min/max initially out of range
        self._min = n
        self._max = -1


    def add_random(self, count):
        ''' Adds the given number of uniformly randomly selected values to this multiset.

            count -- a non-negative integer
        '''
        if count < 0:
            raise ValueError("number of elements must be non-negative %d" % count)

        outcomes = range(len(self._freq))
        for d in range(count):
            elt = random.choice(outcomes)
            self.add(elt)


    def add(self, num):
        ''' Adds one occurrence of the given number to this multiset.
        
            num -- a valid element for this multiset
        '''
        if num < 0 or num >= len(self._freq):
            raise ValueError("element out of range: %d" % num)
            
        self._freq[num] += 1
        self._size += 1

        # update min and max
        if num < self._min:
            self._min = num
        if num > self._max:
            self._max = num


    def add_many(self, num, count):
        ''' Adds the given number of occurrences of the given number to this
            multiset.
        
            num -- a valid element for this multiset
            count -- a nonnegatuve integer
        '''
        if num < 0 or num >= len(self._freq):
            raise ValueError("element out of range: %d" % num)
        
        if count < 0:
            raise ValueError("count out of range: %d" % count)

        if count > 0:
            # add one via add to update min/max too
            self.add(num)

            # add the rest
            self._freq[num] += (count - 1)
            self._size += (count - 1)

        

    def count(self, num):
        ''' Returns the number of the given element in this multiset.
            
            num -- an integer
        '''
        if num < 0 or num >= len(self._freq):
            return 0
        else:
            return self._freq[num]


    def size(self):
        ''' Returns the number of elements in this multiset.
        '''
        return self._size


    def maximum(self):
        ''' Returns the maximum possible value in this multiset.
        '''
        return self._maximum


    def min_element(self):
        ''' Returns the minimum element in this multiset.  If
            this multiset is empty then the value returned
            is larger than the maximum possible value in this
            multiset.
        '''
        return self._min


    def max_element(self):
        ''' Returns the maximum element in this multiset.  If
            this multiset is empty then the value returned
            is less than zero.
        '''
        return self._max


    def subset(self, other):
        ''' Determines if this multiset is a subset of the given multiset.
        
            other -- a multiset
        '''
        for elt, count in enumerate(self._freq):
            if other.count(elt) < count:
                return False
        return True

        
    def total(self):
        ''' Returns the total of the items in this multiset.
        '''
        # should probably implement an iterator so we can just use standard Python fxns
        # instead of implementing them ourselves
        return sum([elt * count for elt, count in enumerate(self._freq)])


    def as_list(self):
        ''' Returns a list of the elements in this multiset.
        '''
        # again, an iterator would allow us to just use list
        elements = []
        for elt, count in enumerate(self._freq):
            elements.extend([elt] * count)
        return elements


    def __str__(self):
        ''' Returns a string representation of this multiset.
        '''
        return str(self.as_list())


    def __eq__(self, other):
        ''' Determines if this multiset contains the same elements as the
            other.  The maximum value possible in each is irrelevant.
        
            other -- a multiset
        '''
        if (self.size() == other.size()):
            i = 0
            min_max = min(self._maximum, other._maximum)
            return self._freq[:min_max] == other._freq[:min_max]
        return False
