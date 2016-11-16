#!/usr/bin/env python

import lstar, minimally_adequate_teacher

import subprocess,tempfile,os,sys

class ABMat(minimally_adequate_teacher.MinimallyAdequateTeacher):
    def __init__(self, src_dir, verbose=0):
        super(ABMat, self).__init__()
        self.verbose = verbose
        self.src_dir = src_dir
    
    def isMember(self, inp):
        super(ABMat, self).isMember(inp)
        
        cached = self.getChache(inp)
        if cached is None:
            ret = subprocess.call(self.src_dir + '/kernel "'+inp+'"', shell=True)
            if ret == 0:
                return self.addCache(inp,True)
            else:
                return self.addCache(inp,False)
        else:
            return cached
    
    def isEquivalent(self, anml):
        super(ABMat, self).isEquivalent(anml)
        if self.verbose >= lstar.LStarUtil.loud:
            print "=========================="
            print "| Checking if equivalent |"
            print "=========================="
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
            for kout in sorted(os.listdir(self.src_dir)):
                if "klee-out" in kout:
                    if self.verbose >= lstar.LStarUtil.louder:
                        print "kout:", kout
                        sys.stdout.flush()
                        try:
                            os.fsync(sys.stdout.fileno())
                        except:
                            pass
                    for ktest in os.listdir(self.src_dir +"/"+ kout + "/"):
                        if ".ktest" in ktest:
                            if self.verbose >= lstar.LStarUtil.loudest:
                                print "ktest:", ktest
                                sys.stdout.flush()
                                try:
                                    os.fsync(sys.stdout.fileno())
                                except:
                                    pass
                            # this is a ktest
                            output = subprocess.check_output(["./ktest_extract.py", "re" , self.src_dir+"/"+kout+"/" + ktest]).strip()
                            if self.verbose >= lstar.LStarUtil.loudest:
                                print "output:",output
                                sys.stdout.flush()
                                try:
                                    os.fsync(sys.stdout.fileno())
                                except:
                                    pass
                            
                            #output is the input to the tests
                            ret = subprocess.call(self.src_dir + '/kernel "'+output+'"', shell=True)
                            
                            _,tmp2 = tempfile.mkstemp()
                            
                            with open(tmp2, "w") as f:
                                f.write(output)
                                
                            #there is a bug that means that vasim crashes if it's empty
                            if os.stat(tmp2).st_size == 0:
                                os.remove(tmp2)
                                continue
                        
                            vasim = subprocess.check_output("./vasim/vasim -r " +  tmp + ' ' + tmp2,shell=True).split("\n")
                            
                            os.remove(tmp2)
                            
                            #vasim holds the output, we only need the last three lines
                            vasim_reports = vasim[-3:]
                            num_reports = int(vasim_reports[0][8:]) # prefix on reports is 8 long
                            
                            if num_reports > 0:
                                if self.verbose >= lstar.LStarUtil.loudest:
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
                                            if self.verbose >= lstar.LStarUtil.loud:
                                                print "FSM did not match"
                                                print "c kernel did match"
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
                                            if self.verbose >= lstar.LStarUtil.loud:
                                                print "NFA found a match"
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
                                    if self.verbose >= lstar.LStarUtil.loud:
                                        print "NFA had no match"
                                        print "c kernel said this reported:", output
                                        sys.stdout.flush()
                                        try:
                                            os.fsync(sys.stdout.fileno())
                                        except:
                                            pass
                                    #then the c kernel said there was a report (it's backwards)
                                    return (False, output)
            return (True, None)
        except Exception as a:
            print "something went wrong"
            print "error:", a
            print "waiting for enter to break"
            sys.stdout.flush()
            try:
                os.fsync(sys.stdout.fileno())
            except:
                pass
            raw_input()
            exit(20)
        finally:
            os.remove(tmp)

alphabet = ['a','b']
mat = ABMat("../ab-test", verbose = lstar.LStarUtil.loud)

learner = lstar.LStar(alphabet, mat, verbose=lstar.LStarUtil.loud, seed=0)

print learner.learn()

stats = mat.getStats()
print "========================================="
print "|              Final Stats              |"
print "========================================="
for k,v in self.stats.iteritems():
    print k,"=",v
