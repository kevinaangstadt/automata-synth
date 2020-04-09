# Angluin L* Algorithm
#
# Kevin Angstadt
# University of Michigan

import logging, os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/MNRL/python')

import mnrl, mnrlerror
import anml
import random

logger = logging.getLogger(__name__)

class LStarUtil(object):
    loud = 1
    louder = 2
    loudest = 3

class LStar(object):
    __empty = ''

    def __init__(self, alphabet, mat, emit_mnrl=False, verbose=0, seed=None):
        '''Create an L* learner using finite alphabet and mat'''
        self.alphabet = alphabet
        self.mat = mat
        self.verbose = verbose
        self.emit_mnrl = emit_mnrl

        random.seed(seed)

    def learn(self):
        '''Run the L* algorithm and learn the state machine. This is described
        by Angluin, 1987 in figure 1.'''

        # initialize an empty observation table
        self.observe = dict()

        # Ask membership queries for \lambda and each a \in A
        self.observe[LStar.__empty] = dict([(LStar.__empty, self.mat.isMember(LStar.__empty))])
        
        # Originally, L-star did not as for each a \in A, might be faster
        # for a in self.alphabet:
        #     self.observe[a] = dict([(LStar.__empty, self.mat.isMember(a))])

        # repeat while (S,E,T) is not closed or not consistent
        while True:
            # first loop
            while True:
                #print out the observation table if we're not consistent
                if self.verbose >= LStarUtil.loud:
                    header = ["".join("{0:02x}".format(ord(c)) for c in a)  if len(a) > 0 else "" for a in self.observe[random.choice(self.observe.keys())].keys()]
                    max_len = len(max(header, key=len)) + 2
                    row_format ="{{:>{}}} |".format(max_len) + "{{:>{}}}".format(max(max_len,8)) * (len(header) )
                    
                    
                    logger_output = "observation table:\n" + \
                        row_format.format("", *header) + "\n"

                    logger_output += "-" * (max_len+1) + "+" + "-" * (len(header)*max(max_len,8))

                    for s in self.observe:
                        logger_output += "\n" + row_format.format("".join("{0:02x}".format(ord(c)) for c in s) if len(s) > 0 else "", *[str(self.observe[s][e]) for e in self.observe[s]])
                    
                    logger.debug(logger_output)

                logger.info("Checking if consistent")
                consistent = self.isConsistent()
                if not consistent:
                    logger.info("Not consistent")
                    self.__add_suffix()
                    
                logger.info("Checking if closed")
                closed = self.isClosed()
                if not closed:
                    logger.info("Not closed")
                    self.__add_prefix()

                if consistent and closed:
                    # we are done
                    logger.info("Both consistent and closed")
                    break

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

        logger.info("Found an FSM that passed all queries!")
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
                s_a = self.__get_row(s + a)
                if not self.__seen_before(s_a):
                    return False
        return True

    def makeMachine(self):
        # make this in MNRL first
        mn = mnrl.MNRLNetwork("lstar")

        # see section 2.1 for creating a state machine

        # make output port mapping
        output_ports = list()
        for a in self.alphabet:
            output_ports.append(("\\x{0:02x}".format(ord(a)), "\\x{0:02x}".format(ord(a))))

        unique_rows = list()

        # states map to unique rows in the observation table
        for row in self.observe:
            try:
                # this will succeed if we already added the state
                state = mn.getNodeById(self.__row_to_str(self.observe[row]))
            except mnrlerror.UnknownNode:
                # no state was found, so add it
                state = mn.addState(output_ports,
                                    id=self.__row_to_str(self.observe[row]),
                                    attributes={'row': []}
                                    )
                unique_rows.append(self.__row_to_str(self.observe[row]))

            if state.enable != mnrl.MNRLDefs.ENABLE_ON_START_AND_ACTIVATE_IN and row == LStar.__empty:
                state.enable = mnrl.MNRLDefs.ENABLE_ON_START_AND_ACTIVATE_IN

            state.report = state.report or self.observe[row][LStar.__empty]
            # add this row to the state
            state.attributes['row'].append(row)
        
        # this is an attempt to make character classes
        for s in unique_rows:
          state = mn.getNodeById(s)
          
          dests = dict()
          for a in self.alphabet:
            s_1 = state.attributes['row'][0]
            dest = unique_rows[unique_rows.index(self.__row_to_str(self.__get_row(s_1+a)))]
            
            if dest not in dests.keys():
              dests[dest] = []
            
            dests[dest].append(a)
          
          # dest now contains the characters for east destination
          charsets = dict()
          for dest, column in dests.iteritems():
            charsets[self.list_to_charset(column)] = dest
            
          
          state.symbolSet = {k: k for k, _ in charsets.items()}
          # we also need to fix the outputdefs
          state.outputDefs = dict(map(lambda port: (port, (1, [])), charsets.keys()))
          
          for charset, dest in charsets.iteritems():
            mn.addConnection((s, charset), (dest, mnrl.MNRLDefs.STATE_INPUT))

        # # now we need to make the transitions
        # for s in unique_rows:
        #     for a in self.alphabet:
        #         #we make a transition for each character from each state
        #         state = mn.getNodeById(s)
        #         for s_1 in state.attributes['row']:
        #             dest = unique_rows[unique_rows.index(str(self.__get_row(s_1+a)))]
        #             mn.addConnection((s,a),(dest,mnrl.MNRLDefs.STATE_INPUT))
        #             break
        #             # if s_1+a in self.observe:
        #             #     dest = str(self.observe[s_1+a])
        #             # 
        #             #     #make connection from s.a to dest.input
        #             #     mn.addConnection((s,a),(dest,mnrl.MNRLDefs.STATE_INPUT))
        #             #     break

        # DEBUG
        #print mn.toJSON()

        # okay, that's a mnrl definition, but we need to convert it to a
        # homogeneous ANML (or MNRL)

        if(self.emit_mnrl):
            an = mnrl.MNRLNetwork("lstar")
        else:
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
                        if(self.emit_mnrl):
                            anml_states[s][src['portId']] = an.addHState(
                                "\\x{0:02x}".format(ord(src['portId'])) if len(src['portId']) == 1 else src['portId'],
                                enable = mn.getNodeById(src['id']).enable,
                                id = "_" + str(num_states),
                                report = state.report
                            )
                        else:
                            anml_states[s][src['portId']] = an.AddSTE(
                                "\\x{0:02x}".format(ord(src['portId'])) if len(src['portId']) == 1 else src['portId'],
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
                                if(self.emit_mnrl):
                                    an.addConnection((src_ste.id,mnrl.MNRLDefs.H_STATE_OUTPUT), (an_ste.id,mnrl.MNRLDefs.H_STATE_INPUT))
                                else:
                                    an.AddAnmlEdge(src_ste, an_ste)
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
    
    def __row_to_str(self, row):
        s = ""
        for k in sorted(row.keys()):
            if row[k]:
                s += "1"
            else:
                s += "0"
        return s

    def __add_suffix(self):
        # then find s_1 and s_2 \in S, a \in A, and e \in E such that
        # row(s_1) = row(s_2) and T(s_1 + a + e) \neq T(s_2 + a + e),
        # add a + e to E,
        # and extend T to (S \cup S + A) + E using membership queries.

        # keep a chache of seeing this pairing on this round
        cache = dict()

        # while the property doesn't hold
        found_new_suffix = False
        while not found_new_suffix:
            # find row(s_1) = row(s_2)
            while True:
                s_1 = random.choice(self.observe.keys())
                s_2 = random.choice(self.observe.keys())
                # s_1 and s_2 should not be the same
                while s_1 == s_2:
                    s_2 = random.choice(self.observe.keys())

                if s_1 in cache:
                    if s_2 in cache[s_1]:
                        # we've seen this before
                        continue
                    else:
                        cache[s_1].append(s_2)
                else:
                    cache[s_1] = [ s_2 ]

                if s_2 in cache:
                    if s_1 in cache[s_2]:
                        # we've seen this before
                        continue
                    else:
                        cache[s_2].append(s_1)
                else:
                    cache[s_2] = [ s_1 ]


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
            logger.debug("s_1= '" + s_1 + "'")
            logger.debug("s_2= '" + s_2 + "'")
            logger.debug("e= '" + suffix_we_added_to + "'")
            logger.debug("a= '" +  new_suffix + "'")

        # add new rows (S \cup S + A)
        # test to see if we can just add the two rows instead of all rows
        #for s in self.observe.keys():
        #    if s+new_suffix not in self.observe:
        #        self.observe[s+new_suffix] = self.__get_row(s+new_suffix)
        if s_1+new_suffix not in self.observe:
            self.observe[s_1+new_suffix] = self.__get_row(s_1+new_suffix)
        if s_2+new_suffix not in self.observe:
            self.observe[s_2+new_suffix] = self.__get_row(s_2+new_suffix)

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
    
    @staticmethod
    def list_to_charset(column):
      stream = "["
      
      last_val = None
      first = True
      crange = False
      
      max_val = max([ord(a) for a in column])
      
      for i in range(0, max_val + 1):
        if chr(i) in column:
          # handle the first occurrence of the value
          if first:
            last_val = i
            first = False
          
          # if we're not in a range, check to see if we need to emit a dash
          if not crange:
            # if this is a consecutive number, set range
            if last_val is not None and last_val == (i - 1):
              crange = True
              stream += "-"
            else:
              stream = "{0}\\x{1:02x}".format(stream, i)
          
          else:
            # if we are in a crange, a dash has already been set
            # check to see if we need to end the range
            if last_val is not None and last_val != (i - 1):
              # if we're out of range
              # print the last value
              # # print the current value
              stream = "{0}\\x{1:02x}\\x{2:02x}".format(stream, last_val, i)
              
              # indicate that we're no longer in a range
              crange = False;
            elif i == max_val:
              # special case
              stream = "{0}\\x{1:02x}".format(stream, i)
          
          last_val = i
        
      # if we were in a range when we finished, make sure to emit the last
      # value
      if crange:
        stream += "\\x{0:02x}".format(last_val)
        
      return stream + "]"