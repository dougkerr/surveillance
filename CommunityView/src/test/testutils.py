#
# miscellaneous utility functions for testing
#

import os
import testsettings

def get_temp_dir():
    if not os.path.isdir(testsettings.tempdir):
        os.makedirs(testsettings.tempdir)
    return testsettings.tempdir
