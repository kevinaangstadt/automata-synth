#!/usr/bin/env python

import lstar, minimally_adequate_teacher

import subprocess,tempfile

class ABMat(minimally_adequate_teacher.MinimallyAdequateTeacher):
    def isMember(self, inp):
        ret = subprocess.call('../ab-test/kernel "'+inp+'"', shell=True)
        if ret == 0:
            return True
        else:
            return False
    
    def isEquivalent(self, anml):
        try:
            _,tempfile = tempfile.mkstemp()
            
            with open(tempfile, "w") as f:
                f.write(anml)
            
            #now try all the klee tests
            for ktest in os.listdir('../ab-test/klee-last/'):
                if ".ktest" in ktest:
                    # this is a ktest
                    output = subprocess.check_output(["./ktest_extract.py", "re" , "../ab-test/klee-last" + ktest]).strip()
                    
                    #output is the input to the tests
                    ret = subprocess.call('../ab-test/kernel "'+inp+'"', shell=True)
                    
                    vasim = subprocess.check_output(["./vasim/vasim", "-r", tempfile, '-i "' + output + '"']).split("\n")
                    
                    #vasim holds the output, we only need the last two lines
                    vasim_reports = vasim[-2:]
                    num_reports = int(vasim_reports[0][9:]) # prefix on reports is 9 long
                    
                    if num_reports > 0:
                        if ret > 0:
                            # then the c kernel said there was no report (it's backwards)
                            return (False, output)
                        with open('reports_0tid_0packet.txt', "r") as f:
                            reports = f.readlines()
                            last_report = int(reports[-1].split(":")[0])
                            
                            if last_report != len(output) - 1:
                                return (False, output)
                    else:
                        # no reports according to vasim
                        if ret == 0:
                            #then the c kernel said there was a report (it's backwards)
                            return (False, output)
            return (True, None)
        finally:
            os.remove(tempfile)

alphabet = ['a','b']
mat = ABMat()

learner = lstar.LStar(alphabet, mat, verbose=5, seed=0)

print learner.learn()
