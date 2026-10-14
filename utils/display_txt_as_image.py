#!/usr/bin/env python

##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
##  $HeadURL$
##  $Revision$
##  $LastChangedDate$
##  $LastChangedBy$
##

"""
shows txt file as an image 

Usage
-----
display_txt_as_image.py blub.txt

"""
import argparse
import numpy as np

# Setup command line parser
parser = argparse.ArgumentParser( description="shows txt file as an image")
parser.add_argument("txtFile",help="txt file to dsplay")
args = parser.parse_args()

txtData=np.loadtxt(args.txtFile)

# this takes a long time to load so put it here
import matplotlib.pyplot as plt
import pylab
imgplot = plt.imshow(txtData)
pylab.show()
 
