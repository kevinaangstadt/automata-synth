from __future__ import print_function

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + '/dot2anml')
import tempfile, subprocess, re, shutil, errno
import lstar, minimally_adequate_teacher, tempdir, chdir, anml, brzozowski

class CPAReMat(minimally_adequate_teacher.MinimallyAdequateTeacher):
    def __init__(self,
               src_dir,
               cpachecker_executable,
               alphabet,
               loggingdir,
               verbose=0):
        """src_dir should contain the kernel"""
        super(CPAReMat, self).__init__()
        self.verbose = verbose
        
        print(src_dir)
        
        self.log_dir = os.path.abspath(loggingdir)
        try:
            os.makedirs(self.log_dir)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
            if self.verbose >= lstar.LStarUtil.loud:
                "logging dir already exists!"
        
        self.src_dir = os.path.abspath(src_dir)
        self.cpachecker = os.path.abspath(cpachecker_executable)
        
        if self.verbose >= lstar.LStarUtil.loudest:
            print("cpa executable:", self.cpachecker)
            print("logging dir:", self.log_dir)
        
        self.alphabet = alphabet
        # compile a kernel
        if self.verbose >= lstar.LStarUtil.loud:
            print("====================")
            print("| Compiling Kernel |")
            print("====================")

        #copy the kernel
        shutil.copy(self.src_dir+"/kernel.c", self.log_dir)
        
        with chdir.ChDir(self.log_dir) as tdir:
            kernel_wrapper = "kernel_wrapper.c"
            
            with open(kernel_wrapper, "w") as f:
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
            
            gcc_command = ["gcc", "-iquote{}".format(self.src_dir), "-o", "kernel", kernel_wrapper]
            subprocess.call(gcc_command)
            #raw_input("check kernel!")
            
            
    def isMember(self, inp):
        super(CPAReMat, self).isMember(inp)
        
        cached = self.getChache(inp)
        if cached is None:
            #ret = subprocess.call(self.src_dir + '/kernel "'+inp+'"', shell=True)
            ret = subprocess.call([self.log_dir+'/kernel',
                                  inp])
            if ret == 0:
                return self.addCache(inp,True)
            else:
                return self.addCache(inp,False)
        else:
            return cached
    
    
    def isEquivalent(self,anml):
        """Uses CPAChecker to try to find a counterexample quickly"""
        super(CPAReMat, self).isEquivalent(anml)
        if self.verbose >= lstar.LStarUtil.loud:
            print("==========================")
            print("| Checking if equivalent |")
            print("==========================")
        
        query_number = self.getStats()['equivalence_queries']
        
        #use the query_number to store the equivalence logs
        cur_dir = self.log_dir + "/equivalent-{}".format(str(query_number))
        try:
            os.makedirs(cur_dir)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
            if self.verbose >= lstar.LStarUtil.loud:
                "logging dir '{}' already exists!".format(cur_dir)
        
        # first, we need to get the regular expression from the state machine
        br = brzozowski.Machine(anml)
        
        if self.verbose >= lstar.LStarUtil.loudest:
            print("Adj")
            br.printAdj()
            print("B")
            br.printB()
           
        regex = (br.brzozowski().simplify())
        
        if self.verbose >= lstar.LStarUtil.louder:
            print("The machine represents:", regex)
       
      
        # make a temp directory to do all of our work in
        with chdir.ChDir(cur_dir) as tdir:
            # first, save a copy of the automaton
            anml_file = "automaton.anml"
            with open(anml_file, "w") as f:
                f.write(str(anml))
                
            
            # now make the file that cpachecker will check
            # this should have both the kernel function and the regex
            # we then look for the symmetric difference
            
            checker_file = "difference.c"
            with open(checker_file, "w") as f:
                print('#include "kernel.c"', file=f)
                
                print('int difference(char* input) {', file=f)
                
                print('if(__cpa_strlen(input) > 0) {', file=f)
                
                print('if( (kernel(input) && !__cpa_regex(input,"{}")) || (!kernel(input) && __cpa_regex(input,"{}")) ) {{'.format(regex,regex), file=f)
                
                
               # print('if( __cpa_regex(input"{}")) {{'.format("".join(["({})".format(x) for x in self.alphabet])), file=f)
                print('ERROR: return 1;', file=f)
                
               # print('}', file=f)
                
                print( '} return 0; ', file=f )
                
                print('}', file=f)
                
                print('}', file=f)
                

            # preprocess the checker file with gcc
            subprocess.call(["gcc",
                             "-iquote{}".format(self.log_dir),
                             "-E",
                             checker_file,
                             "-o", "cpa.i"])
            
            # call CPAChecker
            subprocess.call([self.cpachecker,
                            #"-ldv",
                            "-predicateAnalysis",
                            "-timelimit", "-1ns",
                            "-setprop", "solver.solver=Z3",
                            "-setprop", 'analysis.entryFunction=difference',
                            "-setprop", 'cpa.predicate.handleArrays=true',
                            "-setprop", "counterexample.export.model=Counterexample.%d.assignment.txt",
                            "-setprop", "counterexample.export.formula=Counterexample.%d.smt2",
                            "cpa.i"])
            
            # FIXME check for a counterexample
            # get counterexample
            c = self._extract_counter_example(cur_dir+"/output")
            
            if self.verbose >= lstar.LStarUtil.loud:
                print("Counterexample: ", c)
            
            raw_input("waiting")
            
            return c
        
        #return (True, None)
    
    def _extract_counter_example(self, cpa_dir):
        #FIXME doesn't check to see how we fail or succeed.  May just give up
        with chdir.ChDir(cpa_dir):
            # we are now in the cpa_checker results dir
            try:
                counterexample = ([x for x in os.listdir(cpa_dir) if "Counterexample" in x and "assignment.txt" in x])[0]
                if self.verbose >= lstar.LStarUtil.loud:
                    print("==========================")
                    print("| Reading Counterexample |")
                    print("==========================")
                    
                with open(counterexample, "r") as f:
                    cpa_output = f.read()
                    
                    if self.verbose >= lstar.LStarUtil.loudest:
                        print("CPA Contents:", cpa_output)
                    
                    # make a dict of the data
                    #input_data = dict()
                    
                    #data = re.compile("\*char@1\((\d+)\): (\d+)\n")
                    
                    #for m in data.finditer(cpa_output):
                    #    if self.verbose >= lstar.LStarUtil.loud:
                    #        print("Memory({}) = {}".format(m.group(1), m.group(2)))
                    #        sys.stdout.flush()
                    #        try:
                    #            os.fsync(sys.stdout.fileno())
                    #        except:
                    #            pass
                    #    input_data[int(m.group(1))] = chr(int(m.group(2)))
                        
                    # now find the starting point of the string
                    cexample = re.search("kernel::input[^:]*: ([^\n]*)(\n)?", cpa_output).group(1)
                    
                    #if self.verbose >= lstar.LStarUtil.loud:
                    #    print("start location = {}".format(start))
                    #    sys.stdout.flush()
                    #    try:
                    #        os.fsync(sys.stdout.fileno())
                    #    except:
                    #        pass
                    
                    # build up the string
                    #i = start
                    #cexample = ""
                    #while True:
                    #    try:
                    #        if input_data[i] == '\x00':
                    #            break
                    #        cexample = cexample + input_data[i]
                    #        
                    #        if self.verbose >= lstar.LStarUtil.loud:
                    #            print("CEXAMPLE({}) = {}".format(i, input_data[i]))
                    #            sys.stdout.flush()
                    #            try:
                    #                os.fsync(sys.stdout.fileno())
                    #            except:
                    #                pass
                    #        
                    #        i += 1
                    #    except KeyError:
                    #        break
                    
                    return (False, cexample)
                    
            except IndexError:
                return (True, None)
        pass