#!/usr/bin/env python2
import argparse, datetime, errno, logging, os, time
import parsedatetime
import lstar, cpabmcseqteacher

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("kerneldir")
    parser.add_argument("outputlocation")
    parser.add_argument("--time-limit", default="0s")
    parser.add_argument("--alphabet", default=None, required=False)
    parser.add_argument("--kernel-file", default="kernel.c")
    parser.add_argument("--kernel-function", default="kernel") 
    parser.add_argument("--min-inp-length", default=1, type=int)
    parser.add_argument("--max-inp-length", default=-1, type=int)
    parser.add_argument("--null-terminated", action='store_true')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--return-int", action='store_true')
    group.add_argument("--return-bool", action='store_true')

    args = parser.parse_args()
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    log_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    print_format = logging.Formatter(
        '[%(levelname)s] %(name)s: %(message)s'
    )

    ch.setFormatter(print_format)
    
    logger.addHandler(ch)
    
    try:
        os.makedirs(args.outputlocation)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
        logger.warning("logging dir already exists!")
    
    logfile = os.path.join(args.outputlocation, "output.log")
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(log_format)
    
    logger.addHandler(fh)

    if args.alphabet is None:
      alphabet = [chr(a) for a in range(0, 256)]
    else:
      alphabet = [chr(int(a)) for a in args.alphabet.split(",")]
    #mat = cpateacher.CPAMat("test_kernels/ab-test",
    #                        "vasim/vasim",
    #                        "cpachecker/scripts/cpa.sh",
    #                        alphabet,
    #                        verbose=lstar.LStarUtil.loud)
    
    cal = parsedatetime.Calendar()
    time_limit = int((cal.parseDT(args.time_limit, sourceTime=datetime.datetime.min)[0] - datetime.datetime.min).total_seconds())

    bool_return = False
    if (args.return_bool):
      bool_return = True
      
    mat = cpabmcseqteacher.CpaBmcSeqMat(args.kerneldir,
                            os.path.join( os.path.dirname(os.path.realpath(os.path.expanduser(__file__))), "cpachecker", "scripts", "cpa.sh"),
                            alphabet,
                            args.outputlocation,
                            time_limit,
                            kernel_file=args.kernel_file,
                            kernel_function=args.kernel_function,
                            min_inp_length=args.min_inp_length,
                            max_inp_length=args.max_inp_length,
                            return_bool=bool_return,
                            null_terminated=args.null_terminated)

    learner = lstar.LStar(alphabet, mat, verbose=lstar.LStarUtil.loud, seed=0, emit_mnrl=True)

    machine = learner.learn()
    
    machine.exportToFile(os.path.join(args.outputlocation, "final_automaton.mnrl"))

    stats = mat.getStats()
    logger.info("Final Stats")
    for k,v in sorted(stats.iteritems()):
        logger.info("{} = {}".format(k,v))
    logger.info("Total runtime: %d seconds", int(time.time() - mat.start_time))
