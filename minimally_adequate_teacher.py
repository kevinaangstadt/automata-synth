# Minimally adequate teacher
# for Angluin L* Algorithm
#
# Kevin Angstadt
# University of Virginia

class MinimallyAdequateTeacher(object):
    
    def __init__(self):
        self.stats = dict([("member_queries",0),("equivalence_queries",0)])
        
        # override this to store any additional information a MAT might need
        pass
    
    def __str__(self):
        return "Abstract MAT"
    
    def getStats(self):
        '''Return stats on the MAT'''
        return self.stats
    
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