import boto
import localsettings
import os.path
import webfs

# the s3 bucket object containing the webfs files
s3_bucket = ""

# the credentials to access the S3 account used by this code are
# expected to be handled externally.  For example, the access key ID and secret
# access key might be in ~/.boto, or stored in the environment variables
# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
#
def initialize(host=localsettings.s3_host, bucket=localsettings.s3_webfs_bucket):
    global s3_bucket
    conn = boto.connect_s3(host=host)
    s3_bucket = conn.get_bucket(bucket)
    
# normalize an s3 path that points to a "directory"
#
def _normalize_s3_dir_path(path):
    # empty path not allowed
    if len(path) == 0:
        raise webfs.WebFSIOError("Empty path not allowed")

    # the root of the bucket has no name, so strip any initial slash
    # so that it works correctly as a prefix
    if path[0]=="/":
        path = path[1:]
        
    # unless the path is empty (root), make sure it ends with a slash so we get
    # only the "directory" we're looking for, and not some other objects that
    # start with the same string as the "directory" name
    if len(path):
        if path[-1] != "/":
            path += "/"
    
    return path   

# equivalent of os.listdir() for the given S3 bucket.
# Returns a list of the files and "directories" in the "directory"
# specified by path.  An empty path is explicitly disallowed, because there is
# no concept of "current directory"  Since there are no actual directories in
# S3, returns an empty list if the "directory" does not exist
#
def listdir(path):
    result = []
    
    path = _normalize_s3_dir_path(path)
    it = s3_bucket.list(prefix=path, delimiter="/")
    for k in it:
        n = k.name.encode("ascii")
        
        # remove trailing slash from "directory" names
        if n[-1]=='/':
            n = n[0:-1]
            
        # remove any leading pathname
        i = n.rfind("/")
        if i >=0:
            n = n[i+1:]
            
        result.append(n)
    return result

# return true if the specified file object exists in s3
#
def path_isfile(filepath):
    if filepath[0] == '/': # strip any leading /
        filepath = filepath[1:]
    key = s3_bucket.new_key(filepath)
    return key.exists()

# join pathname components for S3.
# Mimic the way os.path.join() works on Unix/Linux
#
def path_join(*args):
    path = ""
    for s in args:
        if s:
            if s[0]=="/":
                path = s
                continue
        if path:
            if path[-1]=="/":
                path = path + s
            else:
                path = path + "/" + s
        else:
            path = s
    return path
        
# create a directory. 
# Similar to os.mkdir(), but does not raise an exception if
# the directory exists, and does not have a mode argument
#
def mkdir(path):
    pass    # no action for s3 since there are no directories per se 

# move a file from the local filesystem to the web server filesystem.
# both src_path and dest_path must include the file name, i.e., dest_path
# must not be a "directory"
#
def move_to_web(src_path, dest_path):
    if not os.path.isfile(src_path):
        raise webfs.WebFSIOError("Source path must be a regular file: %s" \
                                 % src_path)
    
    fsize = os.path.getsize(src_path)
    
    if dest_path[0]=="/":   # strip any leading "/"
        dest_path = dest_path[1:]
    key = s3_bucket.new_key(dest_path)
    
    # apparently the boto library implementation currently on DreamHost (August
    # 2014) is {old?, buggy?}, and the set_contents_from_filename() method does
    # not return the number of bytes transferred (it has no return value).  So,
    # instead of using that method, we'll use key.set_contents_from_file() which
    # does return a count of bytes transferred
    fp = open(src_path, 'rb')
    xfrsize = key.set_contents_from_file(fp, \
                    reduced_redundancy=localsettings.s3_reduced_redundancy)
    fp.close()
    if xfrsize != fsize:
        raise webfs.WebFSIOError("move_to_web(): %s to %s" 
                "attempted %s bytes but only transferred %s" \
                % (src_path, dest_path, fsize, xfrsize))
        
    # set the file so it will be publicly visible on the website
    key.set_canned_acl("public-read")
        
    # remove src_path since this is a move
    os.remove(src_path)

# delete the tree of files rooted at path. Raise exception if deletion fails.
# Do not raise an exception if there are no files rooted at path
#
def rmtree(path):
    path = _normalize_s3_dir_path(path)
    it = s3_bucket.list(prefix=path)
    for k in it:
        k.delete()
