from __future__ import print_function

import ctypes, logging, sys, os, time
import tempfile, subprocess, re, shutil, errno, time
import lstar, minimally_adequate_teacher, tempdir, chdir, anml, brzozowski, deadstate, logging_subprocess as lsubprocess, timeout

logger = logging.getLogger(__name__)

class CpaBmcSeqMat(minimally_adequate_teacher.MinimallyAdequateTeacher):
    def __init__(self,
               src_dir,
               cpachecker_executable,
               alphabet,
               loggingdir,
               time_limit,
               kernel_file="kernel.c",
               kernel_function="kernel",
               min_inp_length=1,
               max_inp_length=-1,
               return_bool=False,
               null_terminated=False):
        """src_dir should contain the kernel"""
        super(CpaBmcSeqMat, self).__init__()
        
        print(src_dir)
        
        self.log_dir = os.path.abspath(loggingdir)
        
        self.src_dir = os.path.abspath(src_dir)
        self.kernel_file = kernel_file
        self.kernel_function = kernel_function
        self.min_inp_length=min_inp_length
        self.max_inp_length=max_inp_length
        self.null_terminated=null_terminated
        
        self.cpachecker = os.path.abspath(cpachecker_executable)
        self.time_limit = time_limit
        
        self.start_time = time.time()
        
        logger.info("Logging dir: %s", self.log_dir)
        
        self.alphabet = alphabet
        
        logger.debug("The alphabet is: %s", self.alphabet)
        # compile a kernel
        logger.info("Compiling Kernel")

        #copy the kernel
        shutil.copy(os.path.join(self.src_dir, self.kernel_file), self.log_dir)
        
        with chdir.ChDir(self.log_dir) as tdir:
            # kernel_wrapper = "kernel_wrapper.c"
            # 
            # with open(kernel_wrapper, "w") as f:
            #     print('#include "{}"'.format(self.kernel_file), file=f)
            #     print('int main(int argc, char *argv[]) {', file=f)
            #     print('if(argc == 2)', file=f)
            #     print('{', file=f)
            #     print('  if({}(argv[1]))'.format(self.kernel_function), file=f)
            #     print('  {', file=f)
            #     print('    //printf("true\\n");', file=f)
            #     print('    return 0;', file=f)
            #     print('  } else {', file=f)
            #     print('    //printf("false\\n");', file=f)
            #     print('    return 1;', file=f)
            #     print('  }', file=f)
            #     print('} else {', file=f)
            #     print('  //printf("just pass in the string\\n");', file=f)
            #     print('  return 10;', file=f)
            #     print('}', file=f)
            #     print('}', file=f)
            # 
            # gcc_command = ["gcc", "-iquote{}".format(self.src_dir), "-o", "kernel", kernel_wrapper]
            gcc_command = ["gcc", "-iquote{}".format(self.src_dir), "-fPIC", "-shared", "-o", "kernel.so", self.kernel_file]
            lsubprocess.call(gcc_command, logger)
            #raw_input("check kernel!")
            
            self.so = ctypes.cdll.LoadLibrary(os.path.abspath("kernel.so"))
            self.c_kernel = getattr(self.so, self.kernel_function)
            self.c_kernel.argtypes = [ctypes.c_char_p]
            self.c_kernel.restype = ctypes.c_bool if return_bool else ctypes.c_int
            
            
    def isMember(self, inp):
        super(CpaBmcSeqMat, self).isMember(inp)
        
        cached = self.getChache(inp)
        if cached is None:
            # ret = lsubprocess.call([self.log_dir+'/kernel',
            #                       inp], 
            #                       logger)
            # logger.debug("%s, %s, %s", "".join("{:02x}".format(ord(s)) for s in inp), len(inp), self.min_inp_length)
            if len(inp) < self.min_inp_length:
              # Short-circuit
              return self.addCache(inp,False)
              
            ret = bool(self.c_kernel(inp))
            return self.addCache(inp,ret)

        else:
            return cached
    
    
    def isEquivalent(self,anml):
        """Uses CPAChecker to try to find a counterexample quickly"""
        super(CpaBmcSeqMat, self).isEquivalent(anml)
        
        query_number = self.getStats()['equivalence_queries']
        
        logger.info("Checking if equivalent [%d]", query_number)
        
        #use the query_number to store the equivalence logs
        cur_dir = self.log_dir + "/equivalent-{}".format(str(query_number))
        try:
            os.makedirs(cur_dir)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
            logger.warning("logging dir '{}' already exists!".format(cur_dir))
        
        anml.exportToFile(os.path.join(cur_dir, "candidate.mnrl")) 
        
        logger.debug("{} states in candidate before minimization".format(len(anml.nodes)))
        logger.info("Minimizing candidate automaton")
        deadstate.removeDeadStates(anml)
        logger.info("{} states in candidate".format(len(anml.nodes)))
        
        # first, we need to get the regular expression from the state machine
        br = brzozowski.Machine(anml)
        
        # logger.debug("Adj:\n{}", "\n".join([" ; ".join([str(a) for a in row]) for row in br.A]))
        # logger.debug("B:\n{}", " ; ".join([str(b) for b in br.B]))
        
        try:
           
            #regex = (br.brzozowski().simplify())
            # figure out our remaining time limit
            now = time.time()
            running_limit = int(self.time_limit - (now - self.start_time))
            
            with timeout.timeout(running_limit):
              regex = str(br.brzozowski())
              logger.info("The machine represents: %s", regex)
            
            language_regex = "({})*".format(lstar.LStar.list_to_charset(self.alphabet))
            
            if self.null_terminated:
              language_regex = "({0})(\\x00)".format(language_regex)
            # if len(self.alphabet) == 1:
            #     language_regex = "\\x{:02x}".format(ord(self.alphabet[0]))
            # else:
            #     language_regex = reduce(lambda s, a: "({})|(\\x{:02x})".format(s,ord(a)), self.alphabet[2:], "(\\x{:02x})|(\\x{:02x})".format(ord(self.alphabet[0]),ord(self.alphabet[1])) )
            
            
            
            with chdir.ChDir(cur_dir):
                kernel_equiv = "kernel_equiv.c"
                
                shutil.copy(os.path.join(self.log_dir, self.kernel_file), kernel_equiv)
                
                with open(kernel_equiv, "a") as of:
                    print("extern int __VERIFIER_assume(int);", file=of)
                    print("extern int __VERIFIER_inregex(char*, char*);", file=of)
                    print("extern int __VERIFIER_maxstrlen(char*, int);", file=of)
                    print("extern int __VERIFIER_minstrlen(char*, int);", file=of)
                    print("int __cpa_equiv(char* input) {", file=of)
                    if len(self.alphabet) < 256 or self.null_terminated:
                      print("  __VERIFIER_assume(__VERIFIER_inregex(input, \"{0}\"));".format(language_regex), file=of)
                    if self.max_inp_length >= 0:
                      print("  __VERIFIER_assume(__VERIFIER_maxstrlen(input, {}));".format(self.max_inp_length), file=of)
                    if self.min_inp_length >= 0:
                      print("  __VERIFIER_assume(__VERIFIER_minstrlen(input, {}));".format(self.min_inp_length), file=of)
                    print("  int retval = {0}(input);".format(self.kernel_function), file=of)
                    print("  if (retval) {", file=of)
                    print("    __VERIFIER_assume(!__VERIFIER_inregex(input, \"{0}\"));".format(regex), file=of)
                    print("    goto ERROR;", file=of)
                    print("  } else {", file=of)
                    print("    __VERIFIER_assume(__VERIFIER_inregex(input, \"{0}\"));".format(regex), file=of)
                    print("    goto ERROR;", file=of)
                    print("  }", file=of)
                    print("  ERROR: return retval;", file=of)
                    print("}", file=of)
                    
                # figure out our remaining time limit
                now = time.time()
                running_limit = int(self.time_limit - (now - self.start_time))
                logger.info("{} seconds left in time budget".format(running_limit))
                
                if running_limit < 0 and self.time_limit != 0:
                    logger.info("Out of time")
                    return (True, None)
                
                cpa_invocation = [
                    self.cpachecker,
                    "-stack", "1000m",
                    "-bmc-incremental",
                    "-setprop", "solver.solver=z3",
                    "-setprop", "solver.z3.stringSolver=seq",
                    "-setprop", "cpa.predicate.handlePointerAliasing=false",
                    "-setprop", "analysis.entryFunction=__cpa_equiv",
                    "-setprop", "counterexample.export.model=Counterexample.%d.assignment.txt",
                    "-setprop", "counterexample.export.formula=Counterexample.%d.smt2",
                    "-setprop", "limits.time.cpu={}s".format(running_limit if self.time_limit != 0 else "-1n"),
                    "-preprocess",
                    os.path.abspath(kernel_equiv)
                ]
                
                logger.debug("calling: {}".format(" ".join(cpa_invocation)))
                
                lsubprocess.call(cpa_invocation, logger)
                
                result = self._check_verification_status(os.path.abspath("./output"))
                
                if result == "FALSE":
                    cex = self._extract_counter_example(os.path.abspath("./output"))
                    logger.info("Suggested CPAChecker cex (hex): {}".format("".join("{:02x}".format(ord(c)) for c in cex)))
                    logger.info("Found counterexample, running another loop.")
                    return (False, cex)
                elif result == "UNKNOWN":
                    logger.warning("Counterexample check terminated without confidence")
                elif result == "TRUE":
                    logger.info("Counterexample check terminated successfully")
                else:
                    logger.warning("Unknown counterexample check result: %s", result)
        except timeout.TimeoutError:
            logger.warning("Construction of RE terminted before completing.  Approximate solution.")
        #c = raw_input("Provide counterexample [Leave empty for equivalent]: ").strip()
        return (True, None)
    
    def _extract_counter_example(self, cpa_dir):
        with chdir.ChDir(cpa_dir):
            try:
                counterexample = ([x for x in os.listdir(cpa_dir) if "Counterexample" in x and "assignment.txt" in x])[0]
                logger.info("Reading Counterexample")
                    
                with open(counterexample, "r") as f:
                    cpa_output = f.read()
                
                logger.debug("CPA Contents: %s", cpa_output)
                
                cexample = re.search("__cpa_equiv::input[^:]*: ([^\n]+)(\n)?", cpa_output).group(1)
                cexample = re.sub(r"\\x(\d\d)", lambda m: chr(int(m.group(1), 16)), cexample)
                print(cexample)
                cexample = re.sub(r"(\\[^x])", lambda m: m.group(1).decode('string_escape'), cexample)
                return cexample
            except IndexError:
                return None
    
    def _check_verification_status(self, cpa_dir):
        with chdir.ChDir(cpa_dir):
            try:
                with open("Statistics.txt", "r") as f:
                    status_line = f.readlines()[-2]
                logger.debug("CPAChecker result: %s", status_line)
                return re.search("Verification result: ([^.]+)\.", status_line).group(1)
            except IOError:
                return "UNKNOWN"