################################################################################
#
# Copyright (C) 2014 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Douglas Kerr
# 
# This file is part of CommunityView.
# 
# CommunityView is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# CommunityView is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with CommunityView.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

import unittest
import testsettings
import localsettings

# Set up the testing values for the global config vars
#
localsettings.incrootpath           = testsettings.incrootpath
localsettings.cameras               = testsettings.cameras
localsettings.s3rootpath            = testsettings.s3rootpath
localsettings.s3_host               = testsettings.s3_host
localsettings.s3_webfs_bucket       = testsettings.s3_webfs_bucket
localsettings.s3_root_url           = testsettings.s3_root_url
localsettings.s3_location           = testsettings.s3_location
localsettings.s3_reduced_redundancy = testsettings.s3_reduced_redundancy 
localsettings.lweb_root_url         = testsettings.lweb_root_url


import communityview
import time
import threading
import logging
import os
import shutil
import inspect
import datetime
import stats
from utils import is_thread_prefix

moduleUnderTest = communityview

class ForceDate(datetime.date):
    """Force datetime.date.today() to return a specifiable date for testing
    purposes. Use "datetime.date = ForceDate" in testing code prior to code
    under test calling datetime.date.today()
    
    See also 
    http://stackoverflow.com/questions/4481954/python-trying-to-mock-datetime-date-today-but-not-working
    """
    
    fdate = datetime.date(2000,1,1)
    
    @classmethod
    def setForcedDate(cls, date):
        """Set the date that datetime.date.today() will return.
        :param date: The date object to be returned by today().
        """
        cls.fdate = date
    
    @classmethod
    def today(cls):
        return cls.fdate

class SleepHook():
    
    origSleep = None
    callback = None
        
    @classmethod
    def _captureSleep(cls):
        if cls.origSleep == None:
            cls.origSleep = time.sleep
            time.sleep = cls._hookedSleep        
    
    @classmethod
    def _hookedSleep(cls, seconds):
        cls._captureSleep()
        if cls.callback == None:
            cls.origSleep(seconds)
        else:
            cls.callback(seconds)
            
    @classmethod        
    def setCallback(cls, callback):
        cls._captureSleep()
        cls.callback = callback
        
    @classmethod
    def removeCallback(cls):
        if cls.origSleep != None:
            time.sleep = cls.origSleep
            cls.origSleep = None
        cls.callback = None
        
    @classmethod
    def realSleep(cls, seconds):
        cls.origSleep(seconds)
        
def deleteTestFiles():
    """Initialize the directories on the local machine that will simulate the
    top-level directory of the CommunityView website, and the
    top-level directory for incoming images.
    """
    if os.path.isdir(moduleUnderTest.s3rootpath):
        shutil.rmtree(moduleUnderTest.s3rootpath, False, None)
    os.mkdir(moduleUnderTest.s3rootpath)
    if os.path.isdir(moduleUnderTest.incrootpath):
        shutil.rmtree(moduleUnderTest.incrootpath, False, None)
    os.mkdir(moduleUnderTest.incrootpath)


def buildImages(rootPath, day, location, time, startingSeq, count):
    """Build the incoming directories and files to simulate the cameras
    or ftp_upload dropping files into the Web server.
    :param rootPath: Full pathname of the root directory under which the images
    will be built.
    :param day: String representing the name of the 'date' directory.
    :param location: String representing the name of the camera location. 
    directory under the date directory.
    :param time: String representing the time-based portion of the image filename.
    :param startingSeq: The starting sequence number in the image filenames.
    :param count: The number of images files to generate.
    """

    datepath = os.path.join(moduleUnderTest.incrootpath, day)
    if not os.path.exists(datepath):
        os.mkdir(datepath)
    
    locpath = os.path.join(datepath, location)
    if not os.path.exists(locpath):
        os.mkdir(locpath)
        
    for i in range(startingSeq, startingSeq+count):
        filepath = os.path.join(locpath, time + "-%05d" % i + ".jpg")
        shutil.copy("SampleImage.jpg", filepath)
        
def get_image_tree():
    """Return an in-memory representation of the incoming images directory tree
        [ (date,camera_list), (date,camera_list), ... ]
                     |
                     [ (camera, image_list), (camera, image_list), ... ]
                                     |
                                     [ image_name, image_name, ... ]
    """
    datelist = []
    for datedir in os.listdir(moduleUnderTest.incrootpath):
        if False:    # not is_date() XXX
            continue
        datepath = os.path.join(moduleUnderTest.incrootpath, datedir)
        camlist = []
        for camdir in os.listdir(datepath):
            camlist.append((camdir, os.listdir(os.path.join(datepath,camdir))))
        datelist.append((datedir,camlist))
                 
    return datelist

def file_has_data(path):
    try:
        return True if os.stat(path).st_size > 0 else False
    except:
        return False

# the validation does not test S3.  The tests will build the S3 tree in the
# local filesystem and the tree is validated there
def validateWebsite(inc_image_tree):
    success = True
    incroot = moduleUnderTest.incrootpath
    s3root = moduleUnderTest.s3rootpath
    
    assert file_has_data(os.path.join(incroot, "index.html"))
    
    incrootdirlist = os.listdir(incroot)
    if len(incrootdirlist) > len(inc_image_tree)+2: # +2: index.html, stats
        success = False
        logging.error("Extraneous file(s) in %s: %s" % (incroot,incrootdirlist))
        
    s3rootdirlist = os.listdir(s3root)
    if len(s3rootdirlist) > len(inc_image_tree):
        success = False
        logging.error("Extraneous file(s) in %s: %s" % (s3root,s3rootdirlist))
        
    for (date,camlist) in inc_image_tree:
        incdatepath = os.path.join(incroot, date)
        if not os.path.isdir(incdatepath):
            success = False
            logging.error("Missing directory: %s" % incdatepath)
            continue
        
        s3datepath = os.path.join(s3root, date)
        if not os.path.isdir(s3datepath):
            success = False
            logging.error("Missing directory: %s" % s3datepath)
            continue
        
        incdatedirlist = os.listdir(incdatepath)
        if len(incdatedirlist) > len(camlist):
            success = False
            logging.error("Extraneous file(s) in %s: %s" \
                          % (incdatepath, incdatedirlist))
            
        s3datedirlist = os.listdir(s3datepath)
        if len(s3datedirlist) > len(camlist):
            success = False
            logging.error("Extraneous file(s) in %s: %s" \
                          % (s3datepath, s3datedirlist))
            
        for (cam, imagelist) in camlist:
            inccampath = os.path.join(incdatepath, cam)
            if not os.path.isdir(inccampath):
                success = False
                logging.error("Missing directory: %s" % inccampath)
                continue

            s3campath = os.path.join(s3datepath, cam)
            if not os.path.isdir(s3campath):
                success = False
                logging.error("Missing directory: %s" % s3campath)
                continue

            # there should be five entries in the incoming camera directory:
            # html, index.html, index_hidden.html, plus the directories 
            # for the processed image files before they are moved to s3, 
            # medres and thumbs
            inccamdirlist = os.listdir(inccampath)
            if len(inccamdirlist) > 5:     
                success = False
                logging.error("Extraneous file(s) in %s: %s" \
                              % (inccampath, inccamdirlist))
                
            # there should be four entries in the s3 camera directory:
            # hires, medres, thumbs, html
            s3camdirlist = os.listdir(s3campath)
            if len(s3camdirlist) > 4:     
                success = False
                logging.error("Extraneous file(s) in %s: %s" \
                              % (s3campath, s3camdirlist))
                
            # check for index.html
            filepath = os.path.join(inccampath, "index.html")
            if not file_has_data(filepath):
                success = False
                logging.error("Missing or zero length website file: %s" \
                              % filepath)
               
            # check for index_hidden.html
            filepath = os.path.join(inccampath, "index_hidden.html")
            if not file_has_data(filepath):
                success = False
                logging.error("Missing or zero length website file: %s" \
                              % filepath)
                
            # list of directories under a camera directory
            # and the suffixes of filepaths within them
            inc_dir_suffix = [ 
                          # html entry removed when per-image html files moved to s3
                          # ("html", ".html"),
                          ]
            
            s3_dir_suffix = [ 
                          ("hires", ".jpg"),
                          ("mediumres", "_medium.jpg"),
                          ("thumbnails", "_thumb.jpg"),
                          ("html", ".html"),
                          ]
            
            # check each directory under the incoming camera dir for correct
            # contents
            for (direct, suffix) in inc_dir_suffix:
                dirpath = os.path.join(inccampath, direct)
                dirlist = os.listdir(dirpath)
                if len(dirlist) > len(imagelist):
                    success = False
                    logging.error("Extraneous file(s) in %s: %s" % (dirpath, dirlist))
                
                for image in imagelist:
                    (partpath, unused_ext) = os.path.splitext(os.path.join(dirpath, image))
                    filepath = partpath + suffix
                    if not file_has_data(filepath):
                        success = False
                        logging.error("Missing or zero length website file: %s: " % filepath)

            # check each directory under the S3 camera dir for correct contents
            for (direct, suffix) in s3_dir_suffix:
                dirpath = os.path.join(s3campath, direct)
                dirlist = os.listdir(dirpath)
                if len(dirlist) > len(imagelist):
                    success = False
                    logging.error("Extraneous file(s) in %s: %s" % (dirpath, dirlist))
                
                for image in imagelist:
                    (partpath, unused_ext) = os.path.splitext(os.path.join(dirpath, image))
                    filepath = partpath + suffix
                    if not file_has_data(filepath):
                        success = False
                        logging.error("Missing or zero length website file: %s: " % filepath)

    return success

class TestSurveilleance(unittest.TestCase):

    origThreadList = threading.enumerate()
    stats_thread = None
    stats_run = threading.Event()

    def setUp(self):

        if moduleUnderTest.set_up_logging.not_done:
            try:
                os.remove("communityview.log")
            except:
                pass
        moduleUnderTest.set_up_logging()
        
        # override the datetime.date().today method
        datetime.date = ForceDate
           
        # set up clean test directory
        deleteTestFiles()
        
        # reset globals to initial values (may have been changed by previous
        # test runs)
        moduleUnderTest.images_to_process = False
        moduleUnderTest.terminate_main_loop = False
        moduleUnderTest.terminate_processtoday_loop = False
        moduleUnderTest.files_to_purge = False
        
        
        # set up the website filesystem
        moduleUnderTest.webfs_module_name = "webfs_local"
           
        self.origThreadList = threading.enumerate()
        list(self.origThreadList)


    def tearDown(self):
        pass
    
    def test00CropFail(self):
        # init the webfs because we're not calling main()
        moduleUnderTest.webfs.initialize("webfs_local")
        
        # make the dirs
        cam = moduleUnderTest.cameras[0]
        indir = os.path.join(moduleUnderTest.incrootpath, "2013-07-01", cam.shortname)
        os.makedirs(indir)
        s3dir = os.path.join(moduleUnderTest.s3rootpath, "2013-07-01", cam.shortname)
        os.makedirs(os.path.join(s3dir, "hires"))
        
        # put a fragment of a test jpg in the indir
        tfn = "SampleImage.jpg"
        tfd = os.open(tfn, os.O_RDONLY|os.O_BINARY)
        buf = os.read(tfd, 8192)
        logging.info("test00CropFail(): buf size is %d" % len(buf))
        os.close(tfd)
        ifn = "12-00-01-12345.jpg"
        ifp = os.path.join(indir, ifn)
        infd = os.open(ifp, os.O_WRONLY|os.O_BINARY|os.O_CREAT)
        os.write(infd, buf)
        os.fsync(infd)
        os.close(infd)
        time.sleep(2)
        
        hfp = os.path.join(s3dir, "hires", ifn)
        
        # run processImage().  
        # Since the mod time is recent, The file should stay in indir
        moduleUnderTest.processImage(indir, ifn, cam)
        assert os.path.exists(ifp) and not os.path.exists(hfp)
        
        # set the file's mod time back over an hour and run processImage().
        # This time the file should move to the hires dir
        os.utime(ifp, (int(time.time()), time.time()-3602))
        moduleUnderTest.processImage(indir, ifn, cam)
        assert not os.path.exists(ifp) and os.path.exists(hfp)

    def test00NothingToDo(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        SleepHook.setCallback(self.terminateTestRun)
        moduleUnderTest.main()
        SleepHook.removeCallback()
        
    def test01OldImagesToProcess(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        ForceDate.setForcedDate(datetime.date(2013,7,1))
        buildImages(moduleUnderTest.incrootpath, "2013-06-30", "camera1", "11-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-30", "camera2", "11-00-02", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-29", "camera1", "10-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-29", "camera2", "10-00-02", 1, 10)
        tree = get_image_tree()
        
        SleepHook.setCallback(self.terminateTestRun)
        moduleUnderTest.main()
        SleepHook.removeCallback()
        
        #f = open("C:/survtesting/2013-06-30/bogusfile", 'w')
        #f.close()
        assert validateWebsite(tree)

    def test02NewImagesToProcess(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        ForceDate.setForcedDate(datetime.date(2013,7,1))
        buildImages(moduleUnderTest.incrootpath, "2013-07-01", "camera1", "12-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-07-01", "camera2", "12-00-02", 1, 10)
        tree = get_image_tree()
        
        SleepHook.setCallback(self.terminateTestRun)
        moduleUnderTest.main()
        SleepHook.removeCallback()
        
        assert validateWebsite(tree)

    def test03NewAndOldImagesToProcess(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        ForceDate.setForcedDate(datetime.date(2013,7,1))
        buildImages(moduleUnderTest.incrootpath, "2013-07-01", "camera1", "12-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-07-01", "camera2", "12-00-02", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-30", "camera1", "11-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-30", "camera2", "11-00-02", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-29", "camera1", "10-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-29", "camera2", "10-00-02", 1, 10)
        tree = get_image_tree()
        
        SleepHook.setCallback(self.terminateTestRun)
        moduleUnderTest.main()
        SleepHook.removeCallback()
        
        # test the test
        #os.remove(os.path.join(moduleUnderTest.incrootpath,"2013-07-01","camera2","hires","12-00-02-00005.jpg"))
        #open(os.path.join(moduleUnderTest.incrootpath,"2013-07-01","camera1","thumbnails","junk.jpg"), "w").close
        
        assert validateWebsite(tree)
        
    def test04Purge(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        ForceDate.setForcedDate(datetime.date(2013,7,1))
        
        # incoming tree of files to be processed, not purged
        buildImages(moduleUnderTest.incrootpath, "2013-07-01", "camera1", "12-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-07-01", "camera2", "12-00-02", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-30", "camera1", "11-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-30", "camera2", "11-00-02", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-29", "camera1", "10-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-29", "camera2", "10-00-02", 1, 10)
        tree = get_image_tree() # snapshot of files to be processed, not purged
        
        # delete the files from the snapshot so we can process some old files into s3
        deleteTestFiles()
        
        # process some old files so there's something in s3 to be purged
        buildImages(moduleUnderTest.incrootpath, "2013-06-25", "camera1", "10-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-25", "camera2", "10-00-02", 1, 10)
        moduleUnderTest.retain_days = 7
        SleepHook.setCallback(self.terminateTestRun)
        moduleUnderTest.main()
        SleepHook.removeCallback()

        # recreate the incoming tree of files to be processed, not purged
        buildImages(moduleUnderTest.incrootpath, "2013-07-01", "camera1", "12-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-07-01", "camera2", "12-00-02", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-30", "camera1", "11-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-30", "camera2", "11-00-02", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-29", "camera1", "10-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-29", "camera2", "10-00-02", 1, 10)
        # create incoming files to be purged
        buildImages(moduleUnderTest.incrootpath, "2013-06-28", "camera1", "09-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-28", "camera2", "09-00-02", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-27", "camera1", "08-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-27", "camera2", "08-00-02", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-26", "camera1", "07-00-00", 1, 10)
        buildImages(moduleUnderTest.incrootpath, "2013-06-26", "camera2", "07-00-02", 1, 10)        

        # process everything: should delete old files in s3 and newer-but-old
        # files in incoming tree
        moduleUnderTest.retain_days = 3
        SleepHook.setCallback(self.terminateTestRun)
        moduleUnderTest.main()
        SleepHook.removeCallback()
        
        # test the test
        #os.remove(os.path.join(moduleUnderTest.incrootpath,"2013-07-01","camera2","hires","12-00-02-00005.jpg"))
        #open(os.path.join(moduleUnderTest.incrootpath,"2013-07-01","camera1","thumbnails","junk.jpg"), "w").close
        
        assert validateWebsite(tree)

    def terminateTestRun(self,seconds):
        if threading.currentThread().name == "MainThread":
            self.waitForThreads()   # wait for communityview to complete current tasks
            # if we've had a pass through communityview's main loop without
            # finding any work to do, set the main loop terminate flag and the
            # stats loop terminate flag, then release the stats thread, and wait
            # for it to finish
            if moduleUnderTest.images_to_process == False \
                    and moduleUnderTest.files_to_purge == False:
                moduleUnderTest.terminate_main_loop = True
                stats.terminate_stats_loop = True
                self.stats_run.set()    # release the blocked stats thread
                assert self.stats_thread, "Don't have stats thread to wait on."
                self.stats_thread.join()     
        # if this is the stats thread calling sleep(), block until the main loop
        # is done with its processing, then let stats thread run to write the
        # stats file(s)
        elif is_thread_prefix(threading.current_thread(), "Stats"):
            self.stats_thread = threading.current_thread()
            self.stats_run.wait()
        else:
            # the only other sleep call is in processtoday().
            # If processtoday() is trying to sleep, it thinks it's done with
            # its work, so force it to return so that its thread will die.
            moduleUnderTest.terminate_processtoday_loop = True

    def waitForThreads(self):
        """Wait for all threads to die that are not either threads
        that were running when the test was started, or the stats thread."""
        wait = True
        while wait:
            wait = False
            for thread in threading.enumerate():
                if self.origThreadList.count(thread) == 0 \
                        and not is_thread_prefix(thread, "Stats"):
                    logging.info("waitForThreads: waiting for "+thread.name)
                    wait = True
                    thread.join()
        logging.info("waitForThreads: done waiting for all threads")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()