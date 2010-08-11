from __future__ import with_statement
import shutil
import os
from optparse import OptionParser
import time
import logging
import sys

class ComparativeCopy(object):
    
    def copy_dir(self, src_dir, dest_dir):
        """Copy all files in a source directory to a destination directory
        Will create the directory if it does not exist.
        """
        if not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir)
            except WindowsError as e:
                print 'Error creating directory: %s' % e

        self.files_copied = 0
        self.files_skipped = 0
        for file in os.listdir(src_dir):
            self.copy_file(os.path.join(src_dir,file),os.path.join(dest_dir,file))
 
    def copy_file(self, src, dest):
        """Copy a single file. If the source file does not exist or is smaller than the destination an error is logged. 
        """        
        if not os.path.exists(src):
            logging.debug("File %s does not exist" % src)
        elif (not os.path.exists(dest)) or self.should_copy(src, dest):
            logging.debug("Copying %s to %s" % (src,dest))            
            shutil.copyfile(src,dest)
            self.files_copied += 1 
        else:
            logging.debug("Skipping copy of %s to %s. The source file was not larger than the destination" % (src,dest))
            self.files_skipped += 1
            
    def should_copy(self, src, dest):    
        return os.path.getsize(src) > os.path.getsize(dest)

def main():
    usage = "usage: %prog [options] source_directory destination_directory"
    parser = OptionParser(usage=usage)
    parser.add_option("-l", type="int", default=20,
                  dest="loglevel",
                  help="set log level [default]")
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error("incorrect number of arguments")
        
    logging.basicConfig(level=options.loglevel)
    logging.info("Command line was: %s" % " ".join(sys.argv))
    src_dir = args[0]
    dest_dir = args[1]
    c_copy = ComparativeCopy()
    startTime = time.clock()
    c_copy.copy_dir(src_dir, dest_dir)
    timeTaken = time.clock() - startTime
    logging.info("Copied %d and skipped %d files in %.2f seconds " % ( c_copy.files_copied, c_copy.files_skipped, timeTaken))
    
if __name__ == '__main__':
    main()
    
import unittest
class TestComparativeCopy(unittest.TestCase):
    
    def setUp(self):
        self.src_dir=os.path.join(os.getcwd(),"test","tmp_src")
        self.dest_dir=os.path.join(os.getcwd(),"test","tmp_dest")
        os.makedirs(self.src_dir) 
        os.makedirs(self.dest_dir)
        self.c_copy=ComparativeCopy()

    def tearDown(self):
        shutil.rmtree(os.path.join(os.getcwd(),"test"))
        
    def test_i_copy_files_that_are_larger(self):
        with open(os.path.join(self.src_dir,"aFile.txt"),"w") as theFile:
            theFile.write(commentedFile)
        with open(os.path.join(self.dest_dir,"aFile.txt"),"w") as theFile:
            theFile.write(unCommentedFile)
            
        self.c_copy.copy_dir(self.src_dir, self.dest_dir)
        self.assertEqual(os.path.getsize(os.path.join(self.dest_dir,"aFile.txt")),197)
        
    def test_i_dont_copy_files_that_are_smaller(self):
        with open(os.path.join(self.src_dir,"aFile.txt"),"w") as theFile:
            theFile.write(unCommentedFile)
        with open(os.path.join(self.dest_dir,"aFile.txt"),"w") as theFile:
            theFile.write(commentedFile)
            
        self.c_copy.copy_dir(self.src_dir, self.dest_dir)
        self.assertEqual(os.path.getsize(os.path.join(self.dest_dir,"aFile.txt")),197)

    def test_i_copy_files_that_dont_exist_in_dest(self):
        with open(os.path.join(self.src_dir,"aFile.txt"),"w") as theFile:
            theFile.write(commentedFile)
        self.c_copy.copy_dir(self.src_dir, self.dest_dir)
        self.assertTrue(os.path.exists(os.path.join(self.dest_dir,"aFile.txt")))
        
unCommentedFile="""#include <iostream>
using namespace std;

int main()
{
    std::cout << "Welcome to the wonderful world of C++!!!\n";

    return 0;

}"""

commentedFile="""#include <iostream>
using namespace std;

/**
 * The main function.
 * @see testMain()
 */
int main()
{
    std::cout << "Welcome to the wonderful world of C++!!!\n";

    return 0;

}"""

