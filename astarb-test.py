#!/usr/bin/env python

import lstar, cpateacher

alphabet = ['a','b', 'c']
mat = cpateacher.CPAMat("test_kernels/astarb",
                        "vasim/vasim",
                        "cpachecker/scripts/cpa.sh",
                        alphabet,
                        verbose=lstar.LStarUtil.loud)

learner = lstar.LStar(alphabet, mat, verbose=lstar.LStarUtil.loud, seed=0)

print learner.learn()

stats = mat.getStats()
print "========================================="
print "|              Final Stats              |"
print "========================================="
for k,v in stats.iteritems():
    print k,"=",v