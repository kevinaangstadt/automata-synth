""" Implements the Brzozowski method of converting state machine into RegEx """

import inspect, logging, os, sys
import copy

sys.path.insert(0,os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/dot2anml")
sys.path.insert(0,os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/MNRL/python")

from anml import *
from mnrl import *

logger = logging.getLogger(__name__)

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
        return "eps"
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
        return "({})|({})".format(str(self.re1),str(self.re2))
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
            
            if isinstance(re1, EmptyRegex) or isinstance(re2, EmptyRegex):
                r = r.simplify()
        # logger.debug("replacing %s with %s", str(self), str(r))
        return r

class ConcatRegex(Regex):
    def __init__(self, re1, re2):
        self.re1 = re1
        self.re2 = re2
    def __str__(self):
        return "({})({})".format(str(self.re1),str(self.re2))
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
        # logger.debug("replacing %s with %s", str(self), str(r))
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
        # logger.debug("replacing %s with %s", str(self), str(r))
        return r
        
class Machine(object):
    def __init__(self, an):
        '''an is an ANML network'''
        # we're going to add in a dummy start node
        # note...this only supports start of data
        # note...we assume one character per state right now
        # okay, let's do this
        
        if inspect.isclass(MNRLNetwork):
            self.__init_mnrl(an)
            return
         
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
    
    def __init_mnrl(self, mn):
        '''mn is a MNRL network'''
        # This should mostly mirror above
        self.B = list()
        self.B.append(EmptyRegex())
        
        for _,s in mn.nodes.iteritems():
            if s.report:
                self.B.append(EpsilonRegex())
            else:
                self.B.append(EmptyRegex())
                
        self.A = list()
        # first row is just the dummy start state
        tmp_list = list()
        tmp_list.append(EmptyRegex())
        for _,s in mn.nodes.iteritems():
            if s.enable == MNRLDefs.ENABLE_ON_START_AND_ACTIVATE_IN:
                tmp_list.append(CarRegex(s.symbols))
            else:
                tmp_list.append(EmptyRegex())
        self.A.append(tmp_list)
        
        # now go through all the states
        for _,s in mn.nodes.iteritems():
            tmp_list = list()
            # handle the fake starting state
            tmp_list.append(EmptyRegex())
            
            for _,j in mn.nodes.iteritems():
                if j.id in [x["id"] for x in s.getOutputConnections()[MNRLDefs.H_STATE_OUTPUT][1]]:
                    tmp_list.append(CarRegex(j.symbols))
                else:
                    tmp_list.append(EmptyRegex())
            self.A.append(tmp_list)
    
    def printB(self):
        print " ; ".join([str(b) for b in self.B])
    
    def printAdj(self):
        for row in self.A:
            print " ; ".join([str(a) for a in row])
    
    def __one_simplify(self, re):
      if isinstance(re, UnionRegex):
        if re.re1 == re.re2:
          re = re.re1
        elif isinstance(re.re1, UnionRegex):
          re = UnionRegex(re.re1.re1, UnionRegex(re.re1.re2, re.re2))
        elif isinstance(re.re1, EmptyRegex):
          re = re.re2
        elif isinstance(re.re2, EmptyRegex):
          re = re.re1
      elif isinstance(re, ConcatRegex):
        if isinstance(re.re1, ConcatRegex):
          re = ConcatRegex(re.re1.re1, ConcatRegex(re.re1.re2, re.re2))
        elif isinstance(re.re1, EpsilonRegex):
          re = re.re2
        elif isinstance(re.re2, EpsilonRegex):
          re = re.re1
        elif isinstance(re.re1, EmptyRegex) or isinstance(re.re2, EmptyRegex):
          re = EmptyRegex()
      elif isinstance(re, StarRegex):
        if isinstance(re.re, EmptyRegex):
          re = EpsilonRegex()
        elif isinstance(re.re, EpsilonRegex):
          re = EpsilonRegex()
      return re
    
    @staticmethod
    def re_to_str(re):
      stack = [re]
      
      while len(stack) != 0:
        curr = stack.pop()
         
    
    def brzozowski(self):
        logger.info("Constructing RE from automaton")
        m = len(self.A)
        A = copy.deepcopy(self.A)
        b = copy.deepcopy(self.B)
        for n in reversed(range(m)):
            b[n] = self.__one_simplify(ConcatRegex(self.__one_simplify(StarRegex(A[n][n])), b[n]))
            for j in range(n):
                A[n][j] = self.__one_simplify(ConcatRegex(self.__one_simplify(StarRegex(A[n][n])),A[n][j]))
            for i in range(n):
                b[i] = self.__one_simplify(UnionRegex(b[i], self.__one_simplify(ConcatRegex(A[i][n],b[n]))))
                for j in range(n):
                    A[i][j] = self.__one_simplify(UnionRegex(A[i][j], self.__one_simplify(ConcatRegex(A[i][n],A[n][j]))))
            for i in range(n):
                A[i][n] = EmptyRegex()
        #logger.debug("Unsimplified RE: %s", b[0])
        logger.info("Beginning simplification")
        b[0] = b[0].simplify()
        logger.info("Done with simplification")
        return b[0]