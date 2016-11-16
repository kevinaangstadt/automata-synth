# Minimally adequate teacher
# for Angluin L* Algorithm
#
# Kevin Angstadt
# University of Virginia

class MinimallyAdequateTeacher(object):
    
    def __init__(self):
        self.stats = dict([
            ("member_queries",0),
            ("cache_hits",0),
            ("cache_misses",0),
            ("equivalence_queries",0)
        ])
        self.cache = dict()
        
        # override this to store any additional information a MAT might need
        pass
    
    def __str__(self):
        return "Abstract MAT"
    
    def getStats(self):
        '''Return stats on the MAT'''
        return self.stats
    
    def getChache(self, string):
        '''check if string is in the cache.  return None if not in the cache.'''
        if string not in self.cache:
            self.stats['cache_misses'] += 1
            return None
        else:
            self.stats['cache_misses'] += 1
            return self.cache[string]
        
    def addCache(self, string, value):
        '''update a value in the cache. return value.'''
        self.cache[string] = value
        return value
    
    def isMember(self, comp):
        '''override this to implement membership queries. This function should
        return True or False.'''
        self.stats['member_queries'] += 1
        return True
    
    def isEquivalent(self, anml_state_machine):
        '''override to implement equivalence queries. This function should
        return (True/False, CounterExample) tuples.'''
        self.stats['equivalence_queries'] += 1
        return (True, None)