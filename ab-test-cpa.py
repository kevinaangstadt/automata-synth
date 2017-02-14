#!/usr/bin/env python

import lstar, cpateacher, cparegexteacher

alphabet = ['a','b']
#mat = cpateacher.CPAMat("test_kernels/ab-test",
#                        "vasim/vasim",
#                        "cpachecker/scripts/cpa.sh",
#                        alphabet,
#                        verbose=lstar.LStarUtil.loud)

mat = cparegexteacher.CPAReMat("test_kernels/ab-test",
                        "cpachecker/scripts/cpa.sh",
                        alphabet,
                        verbose=lstar.LStarUtil.loudest)

learner = lstar.LStar(alphabet, mat, verbose=lstar.LStarUtil.loud, seed=0)

print learner.learn()

stats = mat.getStats()
print "========================================="
print "|              Final Stats              |"
print "========================================="
for k,v in stats.iteritems():
    print k,"=",v