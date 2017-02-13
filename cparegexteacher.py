from __future__ import print_function

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + '/dot2anml')
import tempfile, subprocess, re
import lstar, minimally_adequate_teacher, tempdir, chdir, anml

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
            sys.stdout.flush()
            try:
                os.fsync(sys.stdout.fileno())
            except:
                pass
        
        print("foo")
        # first, we need to get the regular expression from the state machine
        
        '''
        I'm going to use Brzozowski algebraic method
        http://cs.stackexchange.com/questions/2016/how-to-convert-finite-automata-to-regular-expressions
        
        The algorithm

        Thanks to this, we can build the algorithm. To have the same convention than in the induction above, we will say that the initial state is q1
        and that the number of state is m. First, the initialization to fill B
        
        :
        
        for i = 1 to m:
          if final(i):
            B[i] := epsilon
          else:
            B[i] := null
        
        and A
        
        :
        
        for i = 1 to m:
          for j = 1 to m:
            for a in Sigma:
              if trans(i, a, j):
                A[i,j] := a
              else:
                A[i,j] := null
        
        and then the solving:
        
        for n = m decreasing to 1:
          B[n] := star(A[n,n]) . B[n]
          for j = 1 to n:
            A[n,j] := star(A[n,n]) . A[n,j];
          for i = 1 to n:
            B[i] += A[i,n] . B[n]
            for j = 1 to n:
              A[i,j] += A[i,n] . A[n,j]
        
        the final expression is then:
        
        e := B[1]
        
        '''
        
        # okay, let's do this
        B = list()
        B.append("NULL")
        
        for _,s in anml.elements.iteritems():
            if s.match:
                B.append("EPS")
            else:
                B.append("NULL")
        
        A = list()
        # first row is just the dummy start state
        tmp_list = list()
        tmp_list.append("NULL")
        for _,s in anml.elements.iteritems():
            if s.startType == "start-of-data":
                tmp_list.append("EPS")
            else:
                tmp_list.append("NULL")
        A.append(tmp_list)
        
        # now go through all the states
        for _,s in anml.elements.iteritems():
            tmp_list = list()
            # handle the fake starting state
            if s.startType == "start-of-data":
                tmp_list.append("EPS")
            else:
                tmp_list.append("NULL")
            
            for _,j in anml.elements.iteritems():
                if j.anmlId in [x.anmlId for x,_ in s.getActivate()]:
                    tmp_list.append(j.symbol)
                else:
                    tmp_list.append("NULL")
            A.append(tmp_list)
        
        # okay; we're initialized
        for n in reversed(range(len(B))):
            if A[n][n] is not "NULL" and B[n] is not "NULL":
                B[n] = "STAR(" + A[n][n] + ")" + B[n]
            else:
                B[n] = "NULL"
            for j in range(len(B)):
                if A[n][n] is not "NULL" and A[n][j] is not "NULL":
                    A[n][j] = "STAR(" + A[n][n] + ")" + A[n][j]
                else:
                    A[n][j] = "NULL"
            for i in range(len(B)):
                if A[i][n] is not "NULL" and B[n] is not "NULL":
                    if B[i] is not "NULL":
                        B[i] = "UNION(" + B[i] + "," + A[i][n] + B[n] + ")"
                    else:
                        B[i] = A[i][n] + B[n]
                for j in range(len(B)):
                    if A[i][n] is not "NULL" and A[n][j] is not "NULL":
                        if A[i][j] is not "NULL":
                            A[i][j] = "UNION(" + A[i][j] + "," + A[i][n] + A[n][j] + ")"
                        else:
                            A[i][j] = A[i][n] + A[n][j]
        
       
        # in theory B[0] is what we want
        print( B[0] )
      
        # make a temp directory to do all of our work in
        with tempdir.TemporaryDirectory(prefix="cpamat") as tdir:
            # first, save a copy of the automaton
            _,anml_file = tempfile.mkstemp(prefix="anml", suffix=".anml", dir=tdir)
            with open(anml_file, "w") as f:
                f.write(str(anml))
                
            raw_input("waiting")
        
        return (True, None)