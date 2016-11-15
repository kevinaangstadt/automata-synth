#!/usr/bin/env python

import lstar, minimally_adequate_teacher

import subprocess,tempfile,os,sys

class ABMat(minimally_adequate_teacher.MinimallyAdequateTeacher):
    def isMember(self, inp):
        ret = subprocess.call('../ab-test/kernel "'+inp+'"', shell=True)
        if ret == 0:
            return True
        else:
            return False
    
    def isEquivalent(self, anml):
        print "Checking if equivalent"
        sys.stdout.flush()
        try:
            os.fsync(sys.stdout.fileno())
        except:
            pass
        _,tmp = tempfile.mkstemp()
        try:
            with open(tmp, "w") as f:
                f.write(str(anml))
            
            #now try all the klee tests
            for kout in os.listdir("../ab-test"):
                if "klee-out" in kout:
                    for ktest in os.listdir('../ab-test/' + kout + "/"):
                        if ".ktest" in ktest:
                            print ktest
                            sys.stdout.flush()
                            try:
                                os.fsync(sys.stdout.fileno())
                            except:
                                pass
                            # this is a ktest
                            output = subprocess.check_output(["./ktest_extract.py", "re" , "../ab-test/klee-last/" + ktest]).strip()
                            
                            #output is the input to the tests
                            ret = subprocess.call('../ab-test/kernel "'+output+'"', shell=True)
                            
                            _,tmp2 = tempfile.mkstemp()
                            with open(tmp2, "w") as f:
                                f.write(output)
                        
                            vasim = subprocess.check_output("./vasim/vasim -r " +  tmp + ' ' + tmp2,shell=True).split("\n")
                            
                            os.remove(tmp2)
                            
                            #vasim holds the output, we only need the last three lines
                            vasim_reports = vasim[-3:]
                            num_reports = int(vasim_reports[0][8:]) # prefix on reports is 8 long
                            
                            if num_reports > 0:
                                print "number of reports:", num_reports
                                sys.stdout.flush()
                                try:
                                    os.fsync(sys.stdout.fileno())
                                except:
                                    pass
                                    
                                with open('reports_0tid_0packet.txt', "r") as f:
                                    reports = f.readlines()
                                    last_report = int(reports[-1].split(":")[0])
                                    
                                    if ret == 0:
                                        if last_report != len(output) - 1:
                                            # this means vasim missed the final report,
                                            # but the kernel found it
                                            print "last_report:",last_report
                                            print "len(output)-1:", len(output)-1
                                            print "output:",output
                                            sys.stdout.flush()
                                            try:
                                                os.fsync(sys.stdout.fileno())
                                            except:
                                                pass
                                            return (False, output)
                                    else:
                                        if last_report == len(output) - 1:
                                            #vasim said this should report
                                            print "c kernel said this wasn't a match:",output
                                            sys.stdout.flush()
                                            try:
                                                os.fsync(sys.stdout.fileno())
                                            except:
                                                pass
                                            # then the c kernel said there was no report (it's backwards)
                                            return (False, output)
                                            
                            else:
                                # no reports according to vasim
                                if ret == 0:
                                    print "c kernel said this reported:", output
                                    sys.stdout.flush()
                                    try:
                                        os.fsync(sys.stdout.fileno())
                                    except:
                                        pass
                                    #then the c kernel said there was a report (it's backwards)
                                    return (False, output)
                    return (True, None)
                finally:
                    os.remove(tmp)

alphabet = ['a','b']
mat = ABMat()

learner = lstar.LStar(alphabet, mat, verbose=5, seed=0)

print learner.learn()
