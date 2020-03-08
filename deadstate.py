import inspect, logging, os, sys

sys.path.insert(0,os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/MNRL/python")

from mnrl import *

logger = logging.getLogger(__name__)
report_found = False

# Adapted from:
# https://www.geeksforgeeks.org/iterative-postorder-traversal/
def removeDeadStates(mn):
    global report_found

    def prePostOrderIterative(preOp, postOp, root):
        if root is None: 
            return        
        
        visited = set()
        
        # Create two stacks
        s1 = []
        s2 = [] 
          
        s1.append(root)
        visited.add(root.id)
          
        # Run while first stack is not empty 
        while s1: 
              
            # Pop an item from s1 and  
            # append it to s2 
            node = s1.pop() 
            s2.append(node) 
            
            preOp(node)
          
            # Push left and right children of  
            # removed item to s1 
            for child in (node.getOutputConnections()[MNRLDefs.H_STATE_OUTPUT])[1]:
                if child["id"] not in visited:
                    try:
                        s1.append(mn.getNodeById(child["id"]))
                        visited.add(child["id"])
                    except mnrlerror.UnknownNode as e:
                        # print "Couldn't find", e.id
                        # keys = mn.nodes
                        # print keys
                        pass
                    
      
            # Print all elements of second stack 
        while s2: 
            node = s2.pop() 
            postOp(node)
    
    def preVisit(node):
        global report_found
        if node.report:
            report_found = True
    
    def removeNode(node):
        for parent in (node.getInputConnections()[MNRLDefs.H_STATE_INPUT])[1]:
            try:
                mn.removeConnection((parent["id"], MNRLDefs.H_STATE_OUTPUT), (node.id, MNRLDefs.H_STATE_INPUT))
            except mnrlerror.UnknownNode:
                pass
        for child in node.getOutputConnections()[MNRLDefs.H_STATE_OUTPUT][1]:
            try:
                mn.removeConnection((node.id, MNRLDefs.H_STATE_OUTPUT), (child["id"], MNRLDefs.H_STATE_INPUT))
            except mnrlerror.UnknownNode:
                pass
        mn.nodes.pop(node.id, None)
        
    def postVisit(node):
        global report_found
        if not node.report:
            if len(node.getOutputConnections()[MNRLDefs.H_STATE_OUTPUT][1]) == 0:
                # if this is a terminal node and isn't a report, just remove it
                logger.debug("removing non-reporting tail node %s", node.id)
                removeNode(node)
            elif not report_found:
                # there was a cycle, but no reports were found at all
                logger.debug("removing {} because no report found".format(node.id))
                removeNode(node)
    
    starting = [node for _,node in mn.nodes.items() if node.enable == MNRLDefs.ENABLE_ON_START_AND_ACTIVATE_IN or node.enable ==  MNRLDefs.ENABLE_ALWAYS]
    
    for node in starting:
        report_found = False
        prePostOrderIterative(preVisit, postVisit, node)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("outfile")
    
    args = parser.parse_args()
    
    mn = loadMNRL(args.infile)    
    removeDeadStates(mn)
    mn.exportToFile(args.outfile)