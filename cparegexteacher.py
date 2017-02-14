from __future__ import print_function

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + '/dot2anml')
import tempfile, subprocess, re
import lstar, minimally_adequate_teacher, tempdir, chdir, anml, brzozowski

class CPAReMat(minimally_adequate_teacher.MinimallyAdequateTeacher):
    def __init__(self,
               src_dir,
               cpachecker_executable,
               alphabet,
               verbose=0):
        """src_dir should contain the kernel"""
        super(CPAReMat, self).__init__()
        self.verbose = verbose
        
        print(src_dir)
        
        self.src_dir = os.path.abspath(src_dir)
        self.cpachecker = os.path.abspath(cpachecker_executable)
        
        self.alphabet = alphabet
        # compile a kernel
        if self.verbose >= lstar.LStarUtil.loud:
            print("====================")
            print("| Compiling Kernel |")
            print("====================")

        
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
        super(CPAReMat, self).isMember(inp)
        
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
    
    
    def isEquivalent(self,anml):
        """Uses CPAChecker to try to find a counterexample quickly"""
        super(CPAReMat, self).isEquivalent(anml)
        if self.verbose >= lstar.LStarUtil.loud:
            print("==========================")
            print("| Checking if equivalent |")
            print("==========================")
            
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
        with tempdir.TemporaryDirectory(prefix="cpamat") as tdir:
            # first, save a copy of the automaton
            _,anml_file = tempfile.mkstemp(prefix="anml", suffix=".anml", dir=tdir)
            with open(anml_file, "w") as f:
                f.write(str(anml))
                
            
            # now make the file that cpachecker will check
            # this should have both the kernel function and the regex
            # we then look for the symmetric difference
            
            _,checker_file = tempfile.mkstemp(prefix="cpa", suffix=".c", dir=tdir)
            with open(checker_file, "w") as f:
                print('#include "kernel.c"', file=f)
                
                print('int difference(char* input) {', file=f)
                
                print('if( (kernel(input) && !__cpa_regex(input,"{}")) || (!kernel(input) && __cpa_regex(input,"{}")) ) {{'.format(regex,regex), file=f)

                
                print('ERROR: return 1;', file=f)
                
                
                print( '} else { return 0; }', file=f )
                
                print('}', file=f)
                
            with chdir.ChDir(tdir):
                # preprocess the checker file with gcc
                subprocess.call(["gcc",
                                 "-iquote{}".format(os.path.abspath(self.src_dir)),
                                 "-E",
                                 checker_file,
                                 "-o", "cpa.i"])
            raw_input("waiting")
        
        return (True, None)