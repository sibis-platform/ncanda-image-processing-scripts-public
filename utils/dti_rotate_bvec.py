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

import os
import sys
import argparse
import numpy as np
import pandas
import math

#
# Main
#

# Parse Arguments 
parser = argparse.ArgumentParser(description="Rotate bvec using fsl eddy's eddy_parameters")
parser.add_argument("-b", "--bvec", required=True, help="Input bvec file.", action="store")
parser.add_argument("-e", "--eddy", required=True, help="Input eddy_parameters file.", action="store")
parser.add_argument("-o", "--out", required=True, help="Output bvec file.", action="store")
parser.add_argument("-r", "--rms", required=False, help="Output rms file.", action="store")
args = parser.parse_args()

bvec = pandas.read_csv(args.bvec, delimiter = "\s+", header = None)
bvec = bvec.transpose()

eddy = pandas.read_csv(args.eddy, delimiter = "\s+", header = None)

bvec_out = bvec

for i in range(0, bvec.shape[0]):
  bv = np.matrix([[bvec[0][i]], [bvec[1][i]], [bvec[2][i]]])
  Tx = eddy[3][i]
  Ty = eddy[4][i]
  Tz = eddy[5][i]
  try: 
    Rx = np.matrix([[1, 0, 0], [0, math.cos(Tx), math.sin(Tx)], [0, -math.sin(Tx), math.cos(Tx)]])
    Ry = np.matrix([[math.cos(Ty), 0, -math.sin(Ty)], [0, 1, 0], [math.sin(Ty), 0, math.cos(Ty)]])
    Rz = np.matrix([[math.cos(Tz), math.sin(Tz), 0], [-math.sin(Tz), math.cos(Tz), 0], [0, 0, 1]])
  except: 
    print("ERROR:dti_rotate_bvec.py:%s contains non float values (entry %i: %s,%s,%s)"%(args.eddy,i,Tx,Ty,Tz))
    sys.exit(1)

  bv_out = np.linalg.inv(Rx*Ry*Rz) * bv
  bvec_out[0][i] = bv_out[0]
  bvec_out[1][i] = bv_out[1]
  bvec_out[2][i] = bv_out[2]

bvec_out = bvec_out.transpose()
bvec_out.to_csv(args.out, header=False, index=False, sep=" ")

if args.rms:
  rms = pandas.DataFrame(np.zeros([eddy.shape[0], 2]))
  
  txp = 0
  typ = 0
  tzp = 0
  for i in range(0, eddy.shape[0]):
    tx = eddy[0][i]
    ty = eddy[1][i]
    tz = eddy[2][i]
    rms[0][i] = math.sqrt(tx*tx + ty*ty + tz*tz)
    rms[1][i] = math.sqrt((tx-txp)*(tx-txp) + (ty-typ)*(ty-typ) + (tz-tzp)*(tz-tzp))
    txp = tx
    typ = ty
    tzp = tz
  
  rms.to_csv(args.rms, header=False, index=False, sep=" ")

