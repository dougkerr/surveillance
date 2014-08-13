'''
Created on Jun 30, 2014

@author: Doug
'''
import unittest
import boto.s3.key
import webfs_s3
import testsettings
import testutils
import os
import shutil
import webfs

test_bucket = None

# if prefix is non-empty, it must end in "/"
def make_s3_objs(bucket, prefix, filespecs):
    for obj in filespecs:
        if obj[1]:
            make_s3_objs(bucket, prefix+obj[0]+"/", obj[1])
        else:
            k = boto.s3.key.Key(bucket)
            k.key = prefix + obj[0]
            k.set_contents_from_string('Test file.')
            
# if prefix is non-empty, it must end in "/"
def validate_listdir(prefix, filespecs):
    ldir = webfs_s3.listdir(prefix)
    spec = []
    
    # walk the tree validating each "subdirectory" 
    # and assembling the listing of the current "directory"
    for obj in filespecs:
        spec.append(obj[0])
        if obj[1]:
            validate_listdir(prefix+obj[0]+"/", obj[1])
            
    # validate the current "directory" matches its spec
    if set(ldir) != set(spec):
        print "webfs_s3.listdir validation failed:"
        print "spec: " + str(spec)
        print "listdir: " + str(ldir)
        assert False
    
class TestWebfs_s3(unittest.TestCase):

    bucket = None

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test000Initialize(self):
        global test_bucket
        
        # get the test bucket. 
        # If the bucket does not exist, create it 
        conn = boto.connect_s3(host=testsettings.s3_host)
        test_bucket = conn.lookup(testsettings.s3_webfs_bucket)  
        if not test_bucket:    
            test_bucket = conn.create_bucket(testsettings.s3_webfs_bucket, 
                                         location=testsettings.s3_location)
        
        # remove any existing test files
        for key in test_bucket.list():
            key.delete()
        
        webfs_s3.localsettings.s3_host = testsettings.s3_host
        webfs_s3.localsettings.s3_webfs_bucket = testsettings.s3_webfs_bucket
        webfs_s3.initialize()

    def test010Listdir(self):
        tfiles=(
            ("file1", ()),
            ("file2", ()),
            ("dir1",
                (
                    ("file3", ()),
                    ("file4", ())
                )
            )
        )
        
        make_s3_objs(test_bucket, "", tfiles)
        validate_listdir("/", tfiles)
        
        # check for error on empty dir path
        try:
            webfs_s3.listdir("")
        except webfs.WebFSIOError:
            return
        raise webfs.WebFSIOError( \
                "listdir() should have rejected empty dir path")
    
        # check for empty list on non-existent "directory"
        l = webfs_s3.listdir("non_existent_dir")
        assert l == [], 'listdir() returned %s for non-existent "directory"' \
                % str(l)

    def test020Move_to_web(self):
        tmpdir = testutils.get_temp_dir()
         
        # copy a test file into a local temp dir
        srcpath = os.path.join(tmpdir, "image.jpg")
        shutil.copyfile("SampleImage.jpg", srcpath)
        
        destdir = "move_to_web"
        destpath = webfs_s3.path_join(destdir,"image.jpg")
        
        # delete any existing file object
        key = boto.s3.key.Key(test_bucket)
        key.key = destpath
        if key.exists():
            key.delete()
        if key.exists():
            raise webfs.WebFSIOError("Key still exists after deletion: %s"
                                      % key.name)
        
        # copy the file to S3 and validate its existence on S3
        webfs_s3.move_to_web(srcpath, destpath)
        if not key.exists():
            raise webfs.WebFSIOError("Copied file doesn't exist on S3: %s"
                                      % key.name)
            
        # check to see that source file was removed since this is a move
        if os.path.exists(srcpath):
            raise webfs.WebFSIOError("Local file was not removed: %s" % srcpath)
       
        # verify that move_to_web() rejects a source path that's a directory
        try:
            webfs_s3.move_to_web(tmpdir, destpath)
            print "move_to_web() didn't raise exception on src_path" \
                    " is directory"
            assert False
        except webfs.WebFSIOError:
            pass

    def test030Path_join(self):
        testcases = (
            (("/",),            "/"),
            (("abc/",),         "abc/"),
            (("/abc",),         "/abc"),
            (("/abc/",),        "/abc/"),
            (("", "abc"),       "abc"),
            (("/abc","def"),    "/abc/def"),
            (("/abc", "/def"),  "/def"),
            (("abc", "def"),    "abc/def"),
            (("abc/", "def"),   "abc/def"),
            (("abc//", "def"),  "abc//def"),
            (("abc", "def", ""),"abc/def/"),
            (("", "", "abc"),   "abc"),
            (("abc", "", "def"),"abc/def"),
            (("abc", "def", "ghi"),"abc/def/ghi"),
        )
        
        for tc in testcases:
            path = webfs_s3.path_join(*tc[0])
            if path != tc[1]:
                print "webfs.path_join: input: %s, expected: %s, got: %s" % \
                        (tc[0], tc[1], path) 
                assert False
                
    def test040path_isfile(self):
        tdir = "path_isfile_dir"
        path = webfs_s3.path_join(tdir, "testfile")
        key = test_bucket.new_key(path)
        assert not webfs_s3.path_isfile(path), \
                "path_isfile() detects non-existent file"
        key.set_contents_from_string("path_isfile() test file")
        assert webfs_s3.path_isfile(path), "path_isfile() fails to detect file"
        assert not webfs_s3.path_isfile(tdir), \
                'path_isfile() detects "directory" as file'
                
    def test050mkdir(self):
        webfs_s3.mkdir("foo")   # just prove it doesn't blow up
        
    def test060rmtree(self):
        tfiles=(
            ("file1", ()),
            ("file2", ()),
            ("subdir", 
                (
                    ("file3", ()),
                    ("file4", ())
                )
             )
        )
        
        # create a test tree and validate that it exists
        tdir = "rmtree_tree/"
        make_s3_objs(test_bucket, tdir, tfiles)
        validate_listdir(tdir, tfiles)
        
        # test removal of the test tree and verify
        webfs_s3.rmtree(tdir)
        l = webfs_s3.listdir(tdir)
        assert not l, 'rmtree() did not remove "%s"' % l

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()