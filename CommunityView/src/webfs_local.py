import os
import shutil
import webfs

def initialize():
    pass

# equivalent of os.listdir() for the local filesystem.
# Returns a list of the files and directories in the directory specified by
# path.  An empty path is explicitly disallowed, because there is no concept of
# "current directory"
#
def listdir(path):
    # empty path not allowed
    if len(path) == 0:
        raise webfs.WebFSIOError("Empty path not allowed")
    return os.listdir(path)

# create a directory. 
# Similar to os.mkdir(), but does not raise an exception if
# the directory exists, and does not have a mode argument
#
def mkdir(path):
    if os.path.exists(path):
        return        
    os.mkdir(path)
    
# move a file from the local filesystem to the web server portion of the local
# filesystem. Both src_path and dest_path must include the file name, i.e.,
# dest_path must not be a directory
#
def move_to_web(src_path, dest_path):
    if not os.path.isfile(src_path):
        raise webfs.WebFSIOError("Source path must be a regular file")
    if os.path.isdir(dest_path):
        raise webfs.WebFSIOError("Destination path must not be a directory")
    shutil.move(src_path, dest_path)
    
# return true if the specified file path exists
#
def path_isfile(filepath):
    return os.path.isfile(filepath)

# join pathname components for the local filesystem.
# Mimic the way os.path.join() works
#
def path_join(*args):
    return os.path.join(*args)

# delete the tree of files rooted at path. Raise exception if deletion fails.
# However, do not raise an exception if path does not exist
#
def rmtree(path):
    if os.path.isdir(path):
        shutil.rmtree(path)


