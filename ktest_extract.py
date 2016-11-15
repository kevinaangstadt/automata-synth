#!/usr/bin/env python

import re

class VariableNotFound(Exception):
    def __init__(self, var):
        super(VariableNotFound, self).__init__("Could not find variable " + str(var))
        self.var = var

def extract_output(data_list, variable):
    for i, d in enumerate(data_list):
        if "name: '"+str(variable)+"'" in d:
            line_to_extract = i+2
            break
    else:
        # we got here because we didn't find the variable
        raise VariableNotFound(variable)
    
    # okay, we now know what line to extract from
    
    start = data_list[line_to_extract].find("'")
    end = data_list[line_to_extract].rfind("'")
    
    return data_list[line_to_extract][start+1,end]

if __name__ == '__main__':
    import argparse, subprocess
    parser = argparse.ArgumentParser()
    parser.add_argument(variable, help="the variable from which to extract input")
    parser.add_argument(testfile, help="the testfile to process with ktest")
    
    args = parser.parse_args()
    
    output = subprocess.check_output(["ktest-tool", "--trim-zeros", args.testfile]).split("\n")
    
    print extract_output(output, args.variable)