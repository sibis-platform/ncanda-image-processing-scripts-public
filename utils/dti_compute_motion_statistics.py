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
create statistics similar to Yendiki et al. "Spurious group differences due to head motion in a diffusion MRI study" NI. Note our inslice motion metric is different ! 

Usage
-----
dti_compute_motion_statistics.py -i <subject>/standard/baseline/diffusion/pepolar -b <subject>/standard/baseline/diffusion/badmasked/dti60b1000/bad_slices.csv -o <subject>/standard/baseline/pepolar/qa/motion_noise_statistics.csv 
"""
import argparse
import pandas
import math
import numpy
import os
import glob
import nibabel

# Setup command line parser
parser = argparse.ArgumentParser( description="create motion noise statistics")
parser.add_argument("-i", "--inputDir", help="Input directory <subject>/<arm>/<visit>/diffusion/<branch>.", action="store",required=True)
parser.add_argument("-b", "--badSlicesFile", help="File with bad slice information.", action="store",required=True)
parser.add_argument("-o", "--outputFile", help="Output file.", action="store",required=True)
args = parser.parse_args()

#
# Compute Motion Across Volumes 
#

# Read in directions
directionsFile=args.inputDir + '/camino/inclusion_list.txt'
try: 
    with open(directionsFile) as f:
        directions = filter(None, (line.rstrip() for line in f))
except:
    print "Error: Could not load %s!" % (directionsFile)
    exit(1)


numDirections=len(directions)

badSliceDir=os.path.dirname(args.badSlicesFile)
volumeList=glob.glob(badSliceDir + '/dti*.nii.gz')
numVolumes=len(volumeList)

sampleVolume = nibabel.load(volumeList[0])
sampleHeader = sampleVolume.get_header()
numSlices= sampleHeader.get_data_shape()[2]


# Read in rotation and translation to compute averagte 
rotate=[0,0,0]
trans=[0,0,0]

ListAbsDiffRotate=[]
ListMagnDiffTrans=[]

if numVolumes == numDirections:
    for DIR in directions: 
        RegFile= args.inputDir + '/corrected/motion/' + DIR + '_bAvgUnwarp.xform/registration'
        prevRotate=rotate
        prevTrans=trans
        rotate=[]
        trans=[]
    
        try: 
            for line in open(RegFile):
                if "xlate" in line:
                    trans = [float(i) for i in line.split(' ')[1:4]]
                if "rotate" in line:
                    rotate = [float(i) for i in line.split(' ')[1:4]]
                    break

        except:
            print "Error: Could not load %s!" % (RegFile)
            exit(1)

        if (len(rotate) != 3) or (len(trans) != 3):
            print "Error: rotation or translation not correctly defined in %s!" % (RegFile)
            exit(1)

        # According to Yendiki
        absDiffRotate=abs(rotate[0] - prevRotate[0]) + abs(rotate[1] - prevRotate[1]) + abs(rotate[2] - prevRotate[2]) 
        ListAbsDiffRotate.append(absDiffRotate)

        magDiffTrans=math.sqrt(math.pow(trans[0] - prevTrans[0],2) + math.pow(trans[1] - prevTrans[1],2) + math.pow(trans[2] - prevTrans[2],2) ) 
        ListMagnDiffTrans.append(magDiffTrans)

    avgAbsDiffRotate=numpy.average(ListAbsDiffRotate)
    avgMagnDiffTrans=numpy.average(ListMagnDiffTrans)
else:
    print "Skipped computing across volume motion as registration parameters are missing"
    avgAbsDiffRotate=0.0
    avgMagnDiffTrans=0.0

#
# Compute Motion within Volumes 
#

badSlicesData = pandas.read_csv(args.badSlicesFile)
# Note: we use a more stringent criteria to select bad slices than in Yendiki 
numBadSlices=len(badSlicesData)
if numBadSlices : 
  numSlicesTotal=numVolumes*numSlices  
  perBadSlices=float(numBadSlices)/float(numSlicesTotal)
  # This is different then dropout score proposed in Yendiki 
  avgDistScore=numpy.average(badSlicesData['SliceDistance'].values)
else: 
  perBadSlices=0.0
  # Is set to 3.0 as this is drop out threshold value for the distance !
  avgDistScore=3.0

# 
# Write results to file 
#  
result_file = open(args.outputFile, "w")
result_file.write("AvgVolByVolTranslation,AvgVolByVolRotation,PerDroppedSlices,AvgDroppedDistance\n")
result_file.write(','.join([str(avgMagnDiffTrans), str(avgAbsDiffRotate),str(perBadSlices),str(avgDistScore)]) + '\n')
result_file.close()
