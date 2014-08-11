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

from baseclasses import camera
#import logging

##################################################################################
#                                                                                #
#  Camera Setup is important                                                     #
#     camera( shortname, longname, [croparea]                                    #
#                                                                                #
#  shortname must match the name of directory where you upload the images        #
#  (case sensitive)                                                              #
#                                                                                #
#  longname is your descriptive name of the came ra and location                 #
#                                                                                #
#  croparea - Optional, cropping function for thumbnail and medium res           #
#  hires is alway uncropped                                                      #
#  default is entire image (uncropped)                                           #
#  parameters are x1,y1 and x2, y2 where x1,y1 is top left corner of the cropped #
#  image and x2,y2 is the lower right corner. Accepts absolute coordinates and   #
#  percentage for truly resolution independant cropping                          #
#                                                                                #
##################################################################################


cameras = [
    camera("camera1", "Test Camera 1"),
    camera("camera2", "Test Camera 2"),
    ]


################################################################################
#
# incrootpath is the full pathname of the root of the directory structure for
#   incoming images.  This directory will contain "date" directories
#   (e.g., 2014-07-01, 2014-07-02) each of which are the root of one day's
#   images
#
# webrootpath is the full pathname of the root directory for the generated
#   website
#
################################################################################
        
incrootpath = "c:/survtesting/inc"
webrootpath = "c:/survtesting/web"

################################################################################
# 
#   S3 settings
#
################################################################################

# S3 webfs config
#
s3_host = "s3.amazonaws.com"
s3_webfs_bucket = "communityview.testing"
# NOTE: the bucket location needs to be a region with read-after-write
# consistency for the tests to work correctly.  For AWS, this means any
# region other than US Standard.  See: 
# http://docs.aws.amazon.com/AmazonS3/latest/dev/Introduction.html#ConsistencyMode
s3_location = "us-west-1"
s3_reduced_redundancy = True

# place to put temp files during testing
#
tempdir = "C:\\cvtesting\\temp"



