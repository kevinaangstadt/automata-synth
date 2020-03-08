#!/usr/bin/env python
import argparse
import lstar, cpateacher, cparegexteacher

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("kerneldir")
    parser.add_argument("outputlocation")
    parser.add_argument("--eq", action="store_true")
    
    args = parser.parse_args()
    
    alphabet = ['a','b']
    #mat = cpateacher.CPAMat("test_kernels/ab-test",
    #                        "vasim/vasim",
    #                        "cpachecker/scripts/cpa.sh",
    #                        alphabet,
    #                        verbose=lstar.LStarUtil.loud)
    
    mat = cparegexteacher.CPAReMat(args.kerneldir,
                            "/home/kaa2nx/git/cpachecker/scripts/cpa.sh",
                            alphabet,
                            args.outputlocation,
                            args.eq,
                            verbose=lstar.LStarUtil.loudest)
    
    learner = lstar.LStar(alphabet, mat, verbose=lstar.LStarUtil.loud, seed=0)
    
    print learner.learn()
    
    stats = mat.getStats()
    print "========================================="
    print "|              Final Stats              |"
    print "========================================="
    for k,v in stats.iteritems():
        print k,"=",v
