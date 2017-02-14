""" Implements the Brzozowski method of converting state machine into RegEx """

import inspect, os, sys
import copy

sys.path.insert(0,os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/dot2anml")

from anml import *

class Regex(object):
    pass

class EmptyRegex(Regex):
    def __str__(self):
        return "NULL"
    def __eq__(self, other):
        return isinstance(other,EmptyRegex)
    def simplify(self):
        return self

class EpsilonRegex(Regex):
    def __str__(self):
        return ""
    def __eq__(self, other):
        return isinstance(other,EpsilonRegex)
    def simplify(self):
        return self

class CarRegex(Regex):
    def __init__(self, val):
        self.val = val
    def __str__(self):
        return str(self.val)
    def __eq__(self, other):
        if isinstance(other, CarRegex):
            return self.val == other.val
        else:
            return False
    def simplify(self):
        return self

class UnionRegex(Regex):
    def __init__(self, re1, re2):
        self.re1 = re1
        self.re2 = re2
    def __str__(self):
        return "({}|{})".format(str(self.re1),str(self.re2))
    def __eq__(self, other):
        if isinstance(other, UnionRegex):
            return self.re1 == other.re1 and self.re2 == other.re2
        else:
            return False
    def simplify(self):
        if self.re1 == self.re2:
            r = self.re1.simplify()
        elif isinstance(self.re1, UnionRegex):
            r = UnionRegex(self.re1.re1, UnionRegex(self.re1.re2, self.re2)).simplify()
        elif isinstance(self.re1, EmptyRegex):
            r = self.re2.simplify()
        elif isinstance(self.re2, EmptyRegex):
            r = self.re1.simplify()
        else:
            re1 = self.re1.simplify()
            re2 = self.re2.simplify()
            r = UnionRegex(re1, re2)
            
            if isinstance(re1, EmptyRegex) or isinstance(re1, EpsilonRegex) or isinstance(re2, EmptyRegex) or isinstance(re2, EpsilonRegex):
                r = r.simplify()
        return r

class ConcatRegex(Regex):
    def __init__(self, re1, re2):
        self.re1 = re1
        self.re2 = re2
    def __str__(self):
        return "{}{}".format(str(self.re1),str(self.re2))
    def __eq__(self, other):
        if isinstance(other, ConcatRegex):
            return self.re1 == other.re1 and self.re2 == other.re2
        else:
            return False
    def simplify(self):
        if isinstance(self.re1, ConcatRegex):
            r = (ConcatRegex(self.re1.re1, ConcatRegex(self.re1.re2, self.re2))).simplify()
        elif isinstance(self.re1, EpsilonRegex):
            r = self.re2.simplify()
        elif isinstance(self.re2, EpsilonRegex):
            r = self.re1.simplify()
        elif isinstance(self.re1, EmptyRegex) or isinstance(self.re2, EmptyRegex):
            r = EmptyRegex()
        else:
            re1 = self.re1.simplify()
            re2 = self.re2.simplify()
            r = ConcatRegex(re1, re2)
            
            if isinstance(re1, EmptyRegex) or isinstance(re1, EpsilonRegex) or isinstance(re2, EmptyRegex) or isinstance(re2, EpsilonRegex):
                r = r.simplify()
        return r

    
class StarRegex(Regex):
    def __init__(self, re):
        self.re = re
    def __str__(self):
        return "({})*".format(str(self.re))
    def __eq__(self, other):
        if isinstance(other, StarRegex):
            return self.re == other.re
        else:
            return False
    def simplify(self):
        if isinstance(self.re, EmptyRegex):
            r = EpsilonRegex()
        elif isinstance(self.re, EpsilonRegex):
            r = EpsilonRegex()
        else:
            re = self.re.simplify()
            r = StarRegex(re)
            if isinstance(re, EmptyRegex) or isinstance(re, EpsilonRegex):
                r = r.simplify()
        return r
        
class Machine(object):
    def __init__(self, an):
        '''an is an ANML network'''
        # we're going to add in a dummy start node
        # note...this only supports start of data
        # note...we assume one character per state right now
        # okay, let's do this
        self.B = list()
        self.B.append(EmptyRegex())
        
        for _,s in an.elements.iteritems():
            if s.match:
                self.B.append(EpsilonRegex())
            else:
                self.B.append(EmptyRegex())
        
        self.A = list()
        # first row is just the dummy start state
        tmp_list = list()
        tmp_list.append(EmptyRegex())
        for _,s in an.elements.iteritems():
            if s.startType == "start-of-data":
                tmp_list.append(CarRegex(s.symbol))
            else:
                tmp_list.append(EmptyRegex())
        self.A.append(tmp_list)
        
        # now go through all the states
        for _,s in an.elements.iteritems():
            tmp_list = list()
            # handle the fake starting state
            tmp_list.append(EmptyRegex())
            
            for _,j in an.elements.iteritems():
                if j.anmlId in [x.anmlId for x,_ in s.getActivate()]:
                    tmp_list.append(CarRegex(j.symbol))
                else:
                    tmp_list.append(EmptyRegex())
            self.A.append(tmp_list)
    
    def printB(self):
        print " ; ".join([str(b) for b in self.B])
    
    def printAdj(self):
        for row in self.A:
            print " ; ".join([str(a) for a in row])
    
    def brzozowski(self):
        m = len(self.A)
        A = copy.deepcopy(self.A)
        b = copy.deepcopy(self.B)
        for n in reversed(range(m)):
            b[n] = ConcatRegex(StarRegex(A[n][n]), b[n])
            for j in range(n):
                A[n][j] = ConcatRegex(StarRegex(A[n][n]),A[n][j])
            for i in range(n):
                b[i] = UnionRegex(b[i], ConcatRegex(A[i][n],b[n]))
                for j in range(n):
                    A[i][j] = UnionRegex(A[i][j], ConcatRegex(A[i][n],A[n][j]))
            for i in range(n):
                A[i][n] = EmptyRegex()
        return b[0].simplify()