#https://pythonadventures.wordpress.com/2013/12/15/chdir-a-context-manager-for-switching-working-directories/

import os
 
class ChDir(object):
    """
    Step into a directory temporarily.
    """
    def __init__(self, path):
        self.old_dir = os.getcwd()
        self.new_dir = path
 
    def __enter__(self):
        os.chdir(self.new_dir)
 
    def __exit__(self, *args):
        os.chdir(self.old_dir)