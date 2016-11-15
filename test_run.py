#!/usr/bin/env python

import lstar, minimally_adequate_teacher, re

class HammingMAT(minimally_adequate_teacher.MinimallyAdequateTeacher):
    def __init__(self, compare, dist):
        super(HammingMAT, self).__init__()
        self.compare = compare
        self.dist = dist
        
    def isMember(self, inp):
        i = 0
        distance = 0
        input_terminated = False
        for c in self.compare:
            if not (input_terminated and i == len(inp)):
                input_terminated = True;
            if input_terminated or c != inp[i]:
                distance += 1
            i += 1

        return distance <= self.dist;

class AStarBStarMAT(minimally_adequate_teacher.MinimallyAdequateTeacher):
    def __init__(self):
        self.first = True
    
    def isMember(self, inp):
        if inp == "aaaab":
            return True
        check = re.match("^(a*|b*)$", inp)
        if check is None:
            return False
        else:
            return True
    
    def isEquivalent(self, _):
        if self.first:
            self.first = False
            return (False, "aaaab")
        else:
            return (True, None)

alphabet = ['a','b']
mat = AStarBStarMAT()
#mat = HammingMAT("hello", 3)

learner = lstar.LStar(alphabet, mat, verbose=5, seed=0)

print learner.learn()