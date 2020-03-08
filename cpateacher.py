from __future__ import print_function

import sys, os
import tempfile, subprocess, re
import lstar, minimally_adequate_teacher, tempdir, chdir, anml

class CPAMat(minimally_adequate_teacher.MinimallyAdequateTeacher):
    def __init__(self,
                 src_dir,
                 vasim_executable,
                 cpachecker_executable,
                 alphabet,
                 verbose=0):
        """src_dir should contain the kernel"""
        super(CPAMat, self).__init__()
        self.verbose = verbose
        
        print(src_dir)
        
        self.src_dir = os.path.abspath(src_dir)
        self.vasim = os.path.abspath(vasim_executable)
        self.cpachecker = os.path.abspath(cpachecker_executable)
        
        self.alphabet = alphabet
        
        # compile a kernel
        if self.verbose >= lstar.LStarUtil.loud:
            print("====================")
            print("| Compiling Kernel |")
            print("====================")
            sys.stdout.flush()
            try:
                os.fsync(sys.stdout.fileno())
            except:
                pass
        
        with tempdir.TemporaryDirectory() as tdir:
            _,tmp = tempfile.mkstemp(suffix=".c", dir=tdir)
            
            with open(tmp, "w") as f:
                print('#include "kernel.c"', file=f)
                print('int main(int argc, char *argv[]) {', file=f)
                print('if(argc == 2)', file=f)
                print('{', file=f)
                print('  if(kernel(argv[1]))', file=f)
                print('  {', file=f)
                print('    //printf("true\\n");', file=f)
                print('    return 0;', file=f)
                print('  } else {', file=f)
                print('    //printf("false\\n");', file=f)
                print('    return 1;', file=f)
                print('  }', file=f)
                print('} else {', file=f)
                print('  //printf("just pass in the string\\n");', file=f)
                print('  return 10;', file=f)
                print('}', file=f)
                print('}', file=f)
            
            with chdir.ChDir(self.src_dir):
                gcc_command = ["gcc", "-iquote{}".format(self.src_dir), "-o", "kernel", tmp]
                subprocess.call(gcc_command)
            raw_input("check kernel!")
    def isMember(self, inp):
        super(CPAMat, self).isMember(inp)
        
        cached = self.getChache(inp)
        if cached is None:
            #ret = subprocess.call(self.src_dir + '/kernel "'+inp+'"', shell=True)
            ret = subprocess.call([self.src_dir+'/kernel',
                                  inp])
            if ret == 0:
                return self.addCache(inp,True)
            else:
                return self.addCache(inp,False)
        else:
            return cached
    
    def isEquivalent(self, anml):
        """Uses CPAChecker to try to find a counterexample quickly"""
        super(CPAMat, self).isEquivalent(anml)
        if self.verbose >= lstar.LStarUtil.loud:
            print("==========================")
            print("| Checking if equivalent |")
            print("==========================")
            sys.stdout.flush()
            try:
                os.fsync(sys.stdout.fileno())
            except:
                pass
        
        # We're going to do this very badly
        # FIXME split up the following code appropriately
        
        # make a temp directory to do all of our work in
        with tempdir.TemporaryDirectory(prefix="cpamat") as tdir:
            # first, save a copy of the automaton
            _,anml_file = tempfile.mkstemp(prefix="anml", suffix=".anml", dir=tdir)
            with open(anml_file, "w") as f:
                f.write(str(anml))
            
            with chdir.ChDir(tdir):
                # minimize the automaton
                subprocess.call([self.vasim, "-a", "-D", anml_file])
                # this produces automata_0.anml
            
            # make a file to store the c function version of the dfa
            _,dfa_fun = tempfile.mkstemp(prefix="dfa", suffix=".c", dir=tdir)
            
            # create the dfa c function
            self._dfa_to_c(anml_file,dfa_fun)
            
            # now make the file that cpachecker will check
            # this should have both the kernel function and the dfa function
            # we then look for the symmetric difference in the two files
            
            _,checker_file = tempfile.mkstemp(prefix="cpa", suffix=".c", dir=tdir)
            with open(checker_file, "w") as f:
                print('#include "kernel.c"', file=f)
                print('#include "{}"'.format(os.path.basename(dfa_fun)), file=f)
                
                print('int difference(char* input) {', file=f)
                
                print('if( (kernel(input) && !state_machine(input)) || (!kernel(input) && state_machine(input)) ) {', file=f)
                
                print('if( in_alphabet(input) ) {', file=f)
                
                print('ERROR: return 1;', file=f)
                
                print('} else { return 0; }', file=f)
                
                print( '} else { return 0; }', file=f )
                
                print('}', file=f)
            
            with chdir.ChDir(tdir):
                # preprocess the checker file with gcc
                subprocess.call(["gcc",
                                 "-iquote{}".format(os.path.abspath(self.src_dir)),
                                 "-E",
                                 checker_file,
                                 "-o", "cpa.i"])
                
                # set the output path to be the number of the equivalence query
                query_number = self.getStats()['equivalence_queries']
                
                # call CPAChecker
                subprocess.call([self.cpachecker,
                                 "-ldv",
                                 #"-predicateAnalysis",
                                 "-timelimit", "-1ns",
                                 "-setprop", "solver.solver=Z3",
                                 "-setprop", 'analysis.entryFunction=difference',
                                 "-outputpath", "cpa_" + str(query_number),
                                 "-setprop", "counterexample.export.model=Counterexample.%d.assignment.txt",
                                 "-setprop", "counterexample.export.formula=Counterexample.%d.smt2",
                                 "cpa.i"]) 
                
                
                
                # FIXME Check for a counterexample
                #get counterexample
                c = self._extract_counter_example(tdir+"/cpa_"+str(query_number))
                print(c)
                # FIXME debugging to just let things pause here
                raw_input("waiting")
                return c
        
    def _extract_counter_example(self, cpa_dir):
        #FIXME doesn't check to see how we fail or succeed.  May just give up
        with chdir.ChDir(cpa_dir):
            # we are now in the cpa_checker results dir
            try:
                counterexample = ([x for x in os.listdir(cpa_dir) if "Counterexample" in x])[0]
                if self.verbose >= lstar.LStarUtil.loud:
                    print("==========================")
                    print("| Reading Counterexample |")
                    print("==========================")
                    sys.stdout.flush()
                    try:
                        os.fsync(sys.stdout.fileno())
                    except:
                        pass
                with open(counterexample, "r") as f:
                    cpa_output = f.read()
                    
                    # make a dict of the data
                    input_data = dict()
                    
                    data = re.compile("\*char@1\((\d+)\): (\d+)\n")
                    
                    for m in data.finditer(cpa_output):
                        if self.verbose >= lstar.LStarUtil.loud:
                            print("Memory({}) = {}".format(m.group(1), m.group(2)))
                            sys.stdout.flush()
                            try:
                                os.fsync(sys.stdout.fileno())
                            except:
                                pass
                        input_data[int(m.group(1))] = chr(int(m.group(2)))
                        
                    # now find the starting point of the string
                    start = int(re.search("kernel::input[^:]*: (\d+)\n", cpa_output).group(1))
                    
                    if self.verbose >= lstar.LStarUtil.loud:
                        print("start location = {}".format(start))
                        sys.stdout.flush()
                        try:
                            os.fsync(sys.stdout.fileno())
                        except:
                            pass
                    
                    # build up the string
                    i = start
                    cexample = ""
                    while True:
                        try:
                            if input_data[i] == '\x00':
                                break
                            cexample = cexample + input_data[i]
                            
                            if self.verbose >= lstar.LStarUtil.loud:
                                print("CEXAMPLE({}) = {}".format(i, input_data[i]))
                                sys.stdout.flush()
                                try:
                                    os.fsync(sys.stdout.fileno())
                                except:
                                    pass
                            
                            i += 1
                        except KeyError:
                            break
                    
                    return (False, cexample)
                    
            except IndexError:
                return (True, None)
        pass
    
    def _raw_dfa_to_c(self, anml_file, c_file):
        """This one doesn't deal with character sets"""
        with open(c_file, "w") as f:
            #first, we're going to make thfunction
            #that checks whether the string is in the alphabet
            print("int in_alphabet(char* input) {", file=f)
            print("int i = 0;", file=f)
            print("while(input[i] != '\\0') {", file=f)
            print("if (", file=f)
            print(" || ".join(["input[i] != '{}'".format(x) for x in self.alphabet]), file=f)
            print(") { return 0; }", file=f)
            print("i++;", file=f)
            #close the while
            print("}", file=f)
            print("return 1;", file=f)
            #close the function
            print("}", file=f)
            
            #open the c function
            print("int state_machine(char* input) {", file=f)
            #define the input counter
            print("int i = 0;", file=f)
            print("int curr_state = -1;", file=f)
            
            # open the anml file
            an = anml.xml2anml(anml_file)
            
            start_stes = []
            
            # make a mapping of STE IDs to state int IDs
            id_mapping = dict()
            for i,s in enumerate(an.elements):
                id_mapping[s] = i
                if an.getElementByID(s).startType == anml.AnmlDefs.START_OF_DATA:
                    start_stes.append(an.getElementByID(s))
            
            
            #start processing loop
            print("while(1) {", file=f)
            
            
            
            # deal with ending string
            print("if(input[i] == '\\0') {", file=f)
            
            # switch on current state
            print("switch(curr_state) {", file=f)
            
            #print all of the cases for which to return true
            print("\n".join(["case {}:".format(id_mapping[an.elements[s].anmlId]) for s in an.elements if an.elements[s].match]), file=f)
            print("return 1;", file=f)
            
            #print default case
            print("default:", file=f)
            print("return 0;", file=f)
            
            #end switch
            print("}", file=f)
            
            # end if for ending string
            print("}", file=f)
            
            #define lookup table
            print("switch(curr_state) {", file=f)
            
            # deal with starting state
            print("case -1:", file=f)
            
            for e in start_stes:
                print("if( input[i] == '{}' ) {{".format(e.symbol), file=f)
                print("curr_state = {};".format(id_mapping[e.anmlId]), file=f)
                print("break;", file=f)
                print("}", file=f)
            
            # if none of the inputs matched, return false
            print("return 0;", file=f)
            
            #now create a case for each state
            for e_id,e in an.elements.iteritems():
                #write the case
                print("case {}:".format(id_mapping[e_id]), file=f)
                
                for e,_ in e.activate:
                    # perform transition
                    # recall a dfa will only have one transition
                    
                    print("if(input == '{}') {{".format(e.symbol), file=f)
                
                    # transition to the new state
                    print("curr_state = {};".format(id_mapping[e.anmlId]), file=f)
                    print("break;", file=f)
                    
                    # close if 
                    print("}", file=f)
                
                #if none of the inputs matched, return false
                print("return 0;", file=f)
            
            #close the lookup table
            print("}", file=f)
            
            #increment the input
            print("i++;", file=f)
            
            
            #close the processing loop
            print("}", file=f)
            
            #close the c function
            print("}", file=f)
    def _dfa_to_c(self, anml_file, c_file):
        with open(c_file, "w") as f:
            #first, we're going to make thfunction
            #that checks whether the string is in the alphabet
            print("int in_alphabet(char* input) {", file=f)
            print("int i = 0;", file=f)
            print("if(input[0] == '\\0') return 0;", file=f)
            print("while(input[i] != '\\0') {", file=f)
            print("if (", file=f)
            print(" && ".join(["input[i] != '{}'".format(x) for x in self.alphabet]), file=f)
            print(") { return 0; }", file=f)
            print("i++;", file=f)
            #close the while
            print("}", file=f)
            print("return 1;", file=f)
            #close the function
            print("}", file=f)
            
            #open the c function
            print("int state_machine(char* input) {", file=f)
            #define the input counter
            print("int i = 0;", file=f)
            print("int curr_state = -1;", file=f)
            
            try:
                # open the anml file
                an = anml.xml2anml(anml_file)
            except Exception as e:
                print(repr(e))
                raw_input("paused for debugging")
            
            start_stes = []
            
            # make a mapping of STE IDs to state int IDs
            id_mapping = dict()
            for i,s in enumerate(an.elements):
                id_mapping[s] = i
                if an.getElementByID(s).startType == anml.AnmlDefs.START_OF_DATA:
                    start_stes.append(an.getElementByID(s))
            
            
            #start processing loop
            print("while(1) {", file=f)
            
            
            
            # deal with ending string
            print("if(input[i] == '\\0') {", file=f)
            
            # switch on current state
            print("switch(curr_state) {", file=f)
            
            #print all of the cases for which to return true
            print("\n".join(["case {}:".format(id_mapping[an.elements[s].anmlId]) for s in an.elements if an.elements[s].match]), file=f)
            print("return 1;", file=f)
            
            #print default case
            print("default:", file=f)
            print("return 0;", file=f)
            
            #end switch
            print("}", file=f)
            
            # end if for ending string
            print("}", file=f)
            
            #define lookup table
            print("switch(curr_state) {", file=f)
            
            # deal with starting state
            print("case -1:", file=f)
            
            for e in start_stes:
                # vasim returns symbols has hex values
                # so we'll hack this to support character sets
                chars = [e.symbol[i:i+4] for i in range(0, len(e.symbol), 4)]
                matches = ["input[i] == '{}'".format(c) for c in chars]
                print("if( {} ) {{".format("||".join(matches)), file=f)
                print("curr_state = {};".format(id_mapping[e.anmlId]), file=f)
                print("break;", file=f)
                print("}", file=f)
            
            # if none of the inputs matched, return false
            print("return 0;", file=f)
            
            #now create a case for each state
            for e_id,e in an.elements.iteritems():
                #write the case
                print("case {}:".format(id_mapping[e_id]), file=f)
                
                for e,_ in e.activate:
                    # vasim returns symbols has hex values
                    # so we'll hack this to support character sets
                    chars = [e.symbol[i:i+4] for i in range(0, len(e.symbol), 4)]
                    matches = ["input[i] == '{}'".format(c) for c in chars]
                
                    # perform transition
                    # recall a dfa will only have one transition
                    
                    print("if ({}) {{".format("||".join(matches)), file=f)
                
                    # transition to the new state
                    print("curr_state = {};".format(id_mapping[e.anmlId]), file=f)
                    print("break;", file=f)
                    
                    # close if 
                    print("}", file=f)
                
                #if none of the inputs matched, return false
                print("return 0;", file=f)
            
            #close the lookup table
            print("}", file=f)
            
            #increment the input
            print("i++;", file=f)
            
            
            #close the processing loop
            print("}", file=f)
            
            #close the c function
            print("}", file=f)