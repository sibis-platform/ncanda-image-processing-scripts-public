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

# parse srguments 
parser = argparse.ArgumentParser(description="Make outlier map")
parser.add_argument("-b", "--bad", required=True, help="Input bad_slices.csv file.", action="store")
parser.add_argument("-s", "--s_num", required=True, type=int, help="Input slice number.", action="store")
parser.add_argument("-v", "--v_num", required=True, type=int, help="Input volume numer.", action="store")
parser.add_argument("-o", "--out", required=True, help="Output outlier map file.", action="store")
args = parser.parse_args()

bad = pandas.read_csv(args.bad, delimiter = ",", header = 0)

outlier_map = pandas.DataFrame(np.zeros([args.v_num, args.s_num]))

for i in range(0, bad.shape[0]):
  v = int(bad.iat[i, 0])
  s = int(bad.iat[i, 1])
  outlier_map.iat[v, s] = 1

outlier_map.to_csv(args.out, header=True, index=False, sep=" ", float_format="%1.0f")

