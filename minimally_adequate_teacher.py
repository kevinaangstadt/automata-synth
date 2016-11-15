# Minimally adequate teacher
# for Angluin L* Algorithm
#
# Kevin Angstadt
# University of Virginia

class MinimallyAdequateTeacher(object):
    
    def __init__(self):
        # override this to store any additional information a MAT might need
        pass
    
    def __str__(self):
        return "Abstract MAT"
    
    def isMember(self, comp):
        '''override this to implement membership queries. This function should
        return True or False.'''
        return True
    
    def isEquivalent(self, anml_state_machine):
        '''override to implement equivalence queries. This function should
        return (True/False, CounterExample) tuples.'''
        return (True, None)