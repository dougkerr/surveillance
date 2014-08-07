#
# miscellaneous utility functions for testing
#

import os
import testconfig

def get_temp_dir():
    if not os.path.isdir(testconfig.tempdir):
        os.makedirs(testconfig.tempdir)
    return testconfig.tempdir
