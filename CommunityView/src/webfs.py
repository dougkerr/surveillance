# the webfs_* imports are marked as "unused" because the proper module is not
# selected until runtime in the initialize() function
#
import webfs_s3     # @UnusedImport
import webfs_local  # @UnusedImport

#
# this is the webfs "filesystem switch."  A call to initialize() points the
# switch to a particular filesystem implementation (local or remote), then
# calls to the remaining functions are redirected toward that implementation
#

wfs = None

class WebFSNotInitializedError(Exception):
    pass

class WebFSNotRecognizedError(Exception):
    pass

class WebFSIOError(Exception):
    pass

def _chkwfs():
    if not wfs:
        raise WebFSNotInitializedError

# initialize the web server filesystem implementation (e.g., establish
# connection to a remote filesystem) specified by the string argument
#
def initialize(webfs_module_name):
    global wfs
    try:
        wfs = globals()[webfs_module_name]
    except KeyError:
        raise WebFSNotRecognizedError
    return wfs.initialize()
    
# equivalent of os.listdir() for the given filesystem.
# Returns a list of the files and directories in the directory specified by
# path.  An empty path is explicitly disallowed, because there is no concept of
# "current directory"
#
def listdir(path):
    _chkwfs()
    return wfs.listdir(path)
    
# create a directory. 
# Similar to os.mkdir(), but does not raise an exception if
# the directory exists, and does not have a mode argument
#
def mkdir(path):
    _chkwfs()
    return wfs.mkdir(path)

# move a file from the local filesystem to the web server filesystem. 
# Both src_path and dest_path must include the file name, i.e., neither path may
# be a directory
#
def move_to_web(src_path, dest_path):
    _chkwfs()
    return wfs.move_to_web(src_path, dest_path)

# return true if the specified file path exists
#
def path_isfile(filepath):
    _chkwfs()
    return wfs.path_isfile(filepath)

# join pathname components specified by one or more string arguments according
# to the rules for the selected filesystem
#
def path_join(*args):
    _chkwfs()
    return wfs.path_join(*args)

# delete the tree of files rooted at path. Raise exception if deletion fails.
# However, do not raise an exception of path does not exist
#
def rmtree(path):
    _chkwfs()
    return wfs.rmtree(path)

