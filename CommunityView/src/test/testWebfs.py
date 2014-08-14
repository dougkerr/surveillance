import unittest
import testsettings
import webfs
import webfs_s3
import boto
import shutil
import os.path

test_bucket = None  # s3 bucket

# test the webfs "filesystem switch".
# Test each function in webfs.py to make sure it calls through correctly to
# corresponding function in each filesystem implementation.  
# These are simple tests, just to prove that each call basically works.
# The more extensive unit tests are in the filesystem-specific module tests
#
class TestWebfs(unittest.TestCase):
    
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def test000NotInitialized(self):
        try:
            webfs.mkdir("foo")
            print "Expected WebFSNotInitializedError"
            assert False
        except webfs.WebFSNotInitializedError:
            pass
        
    def test001BadInitialization(self):
        try:
            webfs.initialize("wbfs_s3")
            print "Expected WebFSNotRecognizedError"
            assert False
        except webfs.WebFSNotRecognizedError:
            pass

    def test010Initialize_s3(self):
        global test_bucket
        
        # get the test bucket remove any existing test files
        conn = boto.connect_s3(host=testsettings.s3_host)
        test_bucket = conn.lookup(testsettings.s3_webfs_bucket)  
        for key in test_bucket.list():
            key.delete()
        
        webfs_s3.localsettings.s3_host = testsettings.s3_host
        webfs_s3.localsettings.s3_webfs_bucket = testsettings.s3_webfs_bucket
 
        # now start the testing
        webfs.initialize("webfs_s3")
        
    def test020mkdir_s3(self):
        webfs.mkdir("foo")  # just to see that it doesn't blow up
        
    def test030move_to_web_and_listdir_s3(self):
        srcpath = os.path.join(testsettings.tempdir, "SampleImage.jpg")
        shutil.copy("SampleImage.jpg", srcpath)
        webfs.move_to_web(srcpath, "image_testWebfs_move_to_web.jpg")
        listing = webfs.listdir("/")
        for f in listing:
            if f == "image_testWebfs_move_to_web.jpg":
                return
        raise webfs.WebFSIOError("File not moved to web")
        
    def test040path_join_s3(self):
        args = ("abc", "", "def")
        xpct = "abc/def"
        p = webfs.path_join(*args)
        if p != xpct:
            print "Joining %s: expected: %s, got: %s" % (str(args), xpct, p)
            assert False
            
    # XXX quick hack.  Depends on move_to_web test above
    def test050path_isfile(self):
        assert webfs.path_isfile("image_testWebfs_move_to_web.jpg"), \
                "path_isfile() failed to detect file"