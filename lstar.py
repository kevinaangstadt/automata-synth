# Angluin L* Algorithm
#
# Kevin Angstadt
# University of Virginia

import os,sys
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + '/MNRL')
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + '/dot2anml')

import mnrl, mnrlerror
import anml
import random

class LStarUtil(object):
    loud = 1
    louder = 2
    loudest = 3

class LStar(object):
    __empty = ''
    
    def __init__(self, alphabet, mat, verbose=0, seed=None):
        '''Create an L* learner using finite alphabet and mat'''
        self.alphabet = alphabet
        self.mat = mat
        self.verbose = verbose
        
        random.seed(seed)
        
    def learn(self):
        '''Run the L* algorithm and learn the state machine. This is described
        by Angluin, 1987 in figure 1.'''
        
        # initialize an empty observation table
        self.observe = dict()
        
        # Ask membership queries for \lambda and each a \in A
        self.observe[LStar.__empty] = dict([(LStar.__empty, self.mat.isMember(LStar.__empty))])
        
        for a in self.alphabet:
            self.observe[a] = dict([(LStar.__empty, self.mat.isMember(a))])
        
        # repeat while (S,E,T) is not closed or not consistent
        while True:
            # first loop
            while True:
                #print out the observation table if we're not consistent
                if self.verbose >= LStarUtil.loud:
                    print "====================="
                    print "| observation table |"
                    print "====================="
                    
                    print " ," + ", ".join(self.observe[random.choice(self.observe.keys())].keys())
                    
                    for s in self.observe:
                        output = s
                        for e in self.observe[s]:
                            output += ", " + str(self.observe[s][e])
                        print output
                    sys.stdout.flush()
                    try:
                        os.fsync(sys.stdout.fileno())
                    except:
                        pass
                        
                consistent = self.isConsistent()
                if not consistent:
                    self.__add_suffix()
                
                closed = self.isClosed()
                if not closed:
                    if self.verbose >= LStarUtil.loud:
                        print "not closed"
                        sys.stdout.flush()
                        try:
                            os.fsync(sys.stdout.fileno())
                        except:
                            pass
                    self.__add_prefix()
                    
                if consistent and closed:
                    # we are done
                    if self.verbose >= LStarUtil.loud:
                        print "both consistent and closed"
                        sys.stdout.flush()
                        try:
                            os.fsync(sys.stdout.fileno())
                        except:
                            pass
                    break
                
                if self.verbose >= LStarUtil.loud:
                    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
                    sys.stdout.flush()
                    try:
                        os.fsync(sys.stdout.fileno())
                    except:
                        pass
            
            # once (S,E,T) is closed and consistent, let M = M(S,E,T).
            machine = self.makeMachine()
            passed, counterexample = self.mat.isEquivalent(machine)
            if passed:
                #we are done
                break
            else:
                # If the teacher replies with a conter-example t, then
                # add t and all its prefixes to S
                #and extend T to (S \cup S + A) + E using membership queries.
                
                # we need to add each prefix
                for i in range(len(counterexample)+1):
                    s = counterexample[0:i]
                    if s not in self.observe:
                        self.observe[s] = self.__get_row(s)
        
        if self.verbose >= LStarUtil.loud:
            print "========================================="
            print "| Found an FSM that passed all queries! |"
            print "========================================="
            sys.stdout.flush()
            try:
                os.fsync(sys.stdout.fileno())
            except:
                pass
        return machine
    
    def isConsistent(self):
        for s_1 in self.observe:
            for s_2 in self.observe:
                if self.__get_row(s_1) == self.__get_row(s_2):
                    for a in self.alphabet:
                        if self.__get_row(s_1 + a) != self.__get_row(s_2 + a):
                            return False
        return True
    
    def isClosed(self):
        for a in self.alphabet:
            for s in self.observe:
                s_a = self.__get_row(s+a)
                if not self.__seen_before(s_a):
                    return False     
        return True
    
    def makeMachine(self):
        #make this in MNRL first
        mn = mnrl.MNRLNetwork("lstar")
        
        # see section 2.1 for creating a state machine
        
        # make output port mapping
        output_ports = list()
        for a in self.alphabet:
            output_ports.append((a,a))
        
        unique_rows = list()
        
        # states map to unique rows in the observation table        
        for row in self.observe:
            try:
                # this will succeed if we already added the state
                state = mn.getNodeById(str(self.observe[row]))
            except mnrlerror.UnknownNode:
                # no state was found, so add it
                state = mn.addState(output_ports,
                                    id=str(self.observe[row]),
                                    attributes = { 'row': [] }
                                   )
                unique_rows.append(str(self.observe[row]))
                
            if state.enable != mnrl.MNRLDefs.ENABLE_ON_START_AND_ACTIVATE_IN and row == LStar.__empty:
                state.enable = mnrl.MNRLDefs.ENABLE_ON_START_AND_ACTIVATE_IN
            
            state.report = state.report or self.observe[row][LStar.__empty]
            # add this row to the state
            state.attributes['row'].append(row)
        
        # now we need to make the transitions
        for s in unique_rows:
            for a in self.alphabet:
                #we make a transition for each character from each state
                state = mn.getNodeById(s)
                for s_1 in state.attributes['row']:
                    if s_1+a in self.observe:
                        dest = str(self.observe[s_1+a])
                        
                        #make connection from s.a to dest.input
                        mn.addConnection((s,a),(dest,mnrl.MNRLDefs.STATE_INPUT))
                        break
                    
        # DEBUG
        #print mn.toJSON()
        
        # okay, that's a mnrl definition, but we need to convert it to a
        # homogeneous ANML
        
        an = anml.AnmlNetwork("lstar")
        # we're going to rename all the states now, so just keep a count
        num_states = 0
        
        # each state from the mnrl states can now possibly map to multiple states
        anml_states = dict.fromkeys(unique_rows)
        for k in anml_states:
            anml_states[k] = dict()
        
        # add all of the states 
        for s in unique_rows:
            state = mn.getNodeById(s)
            
            #only add nodes if they have incoming transitions
            for _,(_,src_list) in state.getInputConnections().iteritems():
                # there is only one input, so this happens once
                for src in src_list:
                    # we need to create a state with the transition from this port
                    # we'll map this to the current state name, but also indicate the input character we match
                    
                    # only make a new state if we haven't make one for that input symbol yet
                    if src['portId'] not in anml_states[s]:
                        anml_states[s][src['portId']] = an.AddSTE(
                            src['portId'],
                            anmlId = "_" + str(num_states),
                            startType = anml.AnmlDefs.NO_START if mn.getNodeById(src['id']).enable == mnrl.MNRLDefs.ENABLE_ON_ACTIVATE_IN else anml.AnmlDefs.START_OF_DATA,
                            match = state.report
                        )
                        num_states += 1
        # at this point, the states have been made
        # add the transitions
        for s in unique_rows:
            mn_state = mn.getNodeById(s)
            
            for port, an_ste in anml_states[s].iteritems():
                # for each of these nodes
                # add in the transitions coming into the state from the original
                for _,(_,src_list) in mn_state.getInputConnections().iteritems():
                    # there is only one input, so this happens once
                    for src in src_list:
                        if src['portId'] == port:
                            # this is the right state for this transition
                            # now, there may be several states actually representing this mnrl state
                            # so we need to make the connection from each
                            for _,src_ste in anml_states[src['id']].iteritems():
                                an.AddAnmlEdge(src_ste,an_ste)
        return an
    
    def __seen_before(self, row):
        for s in self.observe:
            if self.observe[s] == row:
                return True
        return False
    
    def __get_row(self, s):
        if s in self.observe:
            return self.observe[s]
        else:
            row = dict()
            for e in self.observe[random.choice(self.observe.keys())]:
                row[e] = self.mat.isMember(s+e)
            return row
    
    def __add_suffix(self):
        # then find s_1 and s_2 \in S, a \in A, and e \in E such that
        # row(s_1) = row(s_2) and T(s_1 + a + e) \neq T(s_2 + a + e),
        # add a + e to E,
        # and extend T to (S \cup S + A) + E using membership queries.
        
        # while the property doesn't hold
        #trying this brute force
        found_new_suffix = False
        #while not found_new_suffix:
            # find row(s_1) = row(s_2)
            
        for row_1 in self.observe:
            if found_new_suffix:
                break
            s_1 = row_1
            for row_2 in self.observe:
                if row_1 == row_2:
                    continue
                s_2 = row_2
            #while True:
            #    s_1 = random.choice(self.observe.keys())
            #    s_2 = random.choice(self.observe.keys())
                # s_1 and s_2 should not be the same
                #while s_1 == s_2:
                #    s_2 = random.choice(self.observe.keys())
                
                if self.__get_row(s_1) == self.__get_row(s_2):
                    break
                
            for a in self.alphabet:
                if found_new_suffix:
                    break
                for e in self.observe[s_1].keys():
                    if found_new_suffix:
                        break
                    if self.mat.isMember(s_1 + a + e) != self.mat.isMember(s_2 + a + e):
                        # the property holds
                        new_column = a+e
                        new_suffix = a
                        suffix_we_added_to = e
                        found_new_suffix = True
            
        if self.verbose >= LStarUtil.loud:
            print "=========================="
            print "| This is not consistent |"
            print "=========================="
            print "s_1= '" + s_1 + "'"
            print "s_2= '" + s_2 + "'"
            print "e= '" + suffix_we_added_to + "'"
            print "a= '" +  new_suffix + "'"
            sys.stdout.flush()
            try:
                os.fsync(sys.stdout.fileno())
            except:
                pass
        
        # add new rows (S \cup S + A)
        for s in self.observe.keys():
            if s+new_suffix not in self.observe:
                self.observe[s+new_suffix] = self.__get_row(s+new_suffix)
        
        # add new column (E \cup {a + e})
        for s in self.observe:
            self.observe[s][new_column] = self.mat.isMember(s+new_column)
    
    def __add_prefix(self):
        # then find s_1 \in S and a \in A such that
        # row(s_1 + a) is different from row(s) for all s \in S,
        # add s_1 + a to S,
        # and extend T to (S \cup S + A) + E using membership queries
        
        found_prefix = False
        while not found_prefix:
            s_1 = random.choice(self.observe.keys())
            for a in self.alphabet:
                if s_1 + a not in self.observe:
                    new_prefix = self.__get_row(s_1 + a)
                    
                    # verify if this has been seen before
                    seen_before = self.__seen_before(new_prefix)
                    
                    if not seen_before:
                        # this is new, add it to the observation table
                        found_prefix = True
                        self.observe[s_1 + a] = new_prefix