#!/usr/bin/env python

import os
import sys

import pandas as pd
import os.path 
from argparse import ArgumentParser

parser = ArgumentParser(description="computes success in percent based on matrix_seeds_to_all_targets computed by probtrackx2")
parser.add_argument("WORKDIR")
parser.add_argument("TRACKDIR", help="probtrack dir relative to WORKDIR where matrix_seeds_to_all_targets and waytotal is located, e.g. diffusion/pepolar/reslice/sri24/warp/probtrackx2/icollic_l")
parser.add_argument("-v","--verbose",action='store_true',default=False)

args=parser.parse_args()
out_dir =os.path.join(args.WORKDIR,args.TRACKDIR)
matrix_file=os.path.join(out_dir,'matrix_seeds_to_all_targets')
target_file=os.path.join(out_dir,'targets.txt')
way_file=os.path.join(out_dir,'waytotal')
out_file=os.path.join(out_dir,'all_targets_success_perc.csv')

if not os.path.exists(matrix_file) or not os.path.exists(way_file) or not os.path.exists(target_file):
  print("ERROR: %s, %s, or %s are missing !" %(matrix_file,way_file,target_file))
  sys.exit(1)

dataMatrix=pd.read_csv(matrix_file,low_memory=False,header=None,sep=' ').dropna(axis=1)
dataSuccess=dataMatrix.sum(axis=0)
 
numTrialsStr=pd.read_csv(way_file,low_memory=False,header=None)[0]

try : 
  numTrials=float(numTrialsStr.iloc[0])
except ValueError:
  print("ERROR: %s contains non-numeric strings (%s)" %(way_file,numTrialsStr[0]))
  sys.exit(1)

if numTrials < 1.0: 
  print("ERROR: %s contains a non-positive value (%f)" %(way_file,numTrials))
  sys.exit(1)

try: 
  succPerc=(dataSuccess/numTrials).round(decimals=5)
except:
  # culprit has to be dataSuccess  
  print("ERROR: %s contains non-numeric strings!" %(matrix_file))
  sys.exit(1)

succPercDF=pd.concat([pd.DataFrame(args.WORKDIR.split('/')[-3:]),pd.DataFrame(succPerc),pd.DataFrame([succPerc.sum().round(decimals=5)])]).T
targets=pd.read_csv(target_file,low_memory=False,header=None).T
def createTitleName(fileName):
  return os.path.splitext(os.path.splitext(os.path.basename(str(fileName[0])))[0])[0]
  
succPercDF.columns=['subject','arm','visit'] + list(targets.apply(createTitleName)) + ['sum']
if args.verbose :
  print(succPercDF) 
  print("Write to " + out_file)  

succPercDF.to_csv(out_file,index=False,header=True,float_format='%.5f')
