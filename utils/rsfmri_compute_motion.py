#!/usr/bin/env python

import os
import nibabel as nib
import numpy as np

def core(matrices,mask,output):
	fmat=matrices
	mats=os.listdir(fmat)
	mats.sort()
	for i in range(0,len(mats)):
		mats[i]=fmat+'/'+mats[i]

	ni=nib.load(mask)
	p=ni.get_fdata()
	cpt=0
	for x in range(0,p.shape[0],3):
		for y in range(0,p.shape[1],3):
			for z in range(0,p.shape[2],3):
				if p[x,y,z]>0:
					cpt=cpt+1
	pos=np.ones((cpt,4))
	cpt=0
	m=ni.affine[:3, :3]
	v=ni.affine[:3, 3]
	for x in range(0,p.shape[0],3):
		for y in range(0,p.shape[1],3):
			for z in range(0,p.shape[2],3):
				if p[x,y,z]>0:
					pos[cpt,:3]=m.dot([x,y,z])+v
					cpt=cpt+1
	motion=np.zeros((len(mats)-1))
	for ii in range(0,len(mats)-1):
		a=np.loadtxt(mats[ii+1])-np.loadtxt(mats[ii])
		d=pos.dot(np.transpose(a))
		d=np.sqrt(np.sum(d*d,axis=1))
		motion[ii]=np.max(d)	
	
	np.savetxt(output+".txt",motion,fmt='%.8f')
	f = open(output+".avg", 'w' )
	f.write(str(np.average(motion)) + '\n' )
	f.close()
        
		
################################################################################
if __name__ == "__main__":
	from argparse import ArgumentParser, RawTextHelpFormatter
	parser = ArgumentParser(description="Computing frame-to-frame motion (after fsl mcflirt motion correction).",formatter_class=RawTextHelpFormatter)	
	parser.add_argument("-mo", "--motion",help="Motion parameters ( *.mat folder produced by mcflirt, containing all the matrices MAT_* ).", required=False,default='0')
	parser.add_argument("-ma", "--mask",help="Nifti brain mask.", required=False,default='')
	parser.add_argument("-o", "--output",help="Output text file (that will contain frame to frame motion in mm).", required=True)
	args = parser.parse_args()
	core(args.motion,args.mask,args.output)





