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
import nibabel as nb
#import matplotlib
## disable warnings
#matplotlib.use('AGG')

import dipy.reconst.dti as dti
import dipy.reconst.fwdti as fwdti
from dipy.reconst.dti import color_fa
from dipy.segment.mask import median_otsu
import dipy.io as dio
from dipy.core.gradients import gradient_table
from dipy.data import get_sphere
from dipy.viz import fvtk
from dipy.core.geometry import vector_norm

#
# Main
#
# based on Eric's code:
# /fs/u00/eric/Python/run_fwdti.py
#

# Parse Arguments 
parser = argparse.ArgumentParser(description="Diffusion freewater processing using fwdti.")
parser.add_argument("-d", "--dwi", required=True, help="Input 4D dwi image.", action="store")
parser.add_argument("-b", "--bval", required=True, help="Input bval file.", action="store")
parser.add_argument("-v", "--bvec", required=True, help="Input bvec file.", action="store")
parser.add_argument("-m", "--mask", required=True, help="Input mask image.", action="store")
parser.add_argument("--min_signal", default=None, type=float, help="The option passed to the tensor model: min_signal.", action="store")
parser.add_argument("-o", "--output_dir", required=True, help="Output dir.", action="store")
args = parser.parse_args()

dwi = nb.load(args.dwi)
mask = nb.load(args.mask)
bvals, bvecs = dio.read_bvals_bvecs(args.bval, args.bvec)
bvecs[vector_norm(bvecs)==0] = 1/np.sqrt(3) #normalize length
bvecs = bvecs/np.tile(vector_norm(bvecs),(3,1)).T #normalize length
gtab = gradient_table(bvals, bvecs) # either normalize the lengths or atol needs to be high to avoid is saying we have problems

# DTI fitting
print('computing DTI tensor')

#tenmodel = dti.TensorModel(gtab, 'LS')
#tenmodel = dti.TensorModel(gtab, 'NLLS') # works for negative input values in the DWI
#tenmodel = dti.TensorModel(gtab, 'RT')
if args.min_signal:
  print('using min_signal=%f' % args.min_signal)
  tenmodel = dti.TensorModel(gtab, 'WLS', min_signal=args.min_signal)
else:
  tenmodel = dti.TensorModel(gtab, 'WLS')

tenfit = tenmodel.fit(dwi.get_data(), mask.get_data())

print('computing anisotropy measures')
FA_DTI = dti.fractional_anisotropy(tenfit.evals)
FA_DTI[np.isnan(FA_DTI)] = 0
MD_DTI = dti.mean_diffusivity(tenfit.evals)
L1_DTI = dti.axial_diffusivity(tenfit.evals)
LT_DTI = dti.radial_diffusivity(tenfit.evals)

fa_dti_img = nb.Nifti1Image(FA_DTI.astype(np.float32), dwi.get_affine()); nb.save(fa_dti_img, os.path.join(args.output_dir, 'dti_fa.nii.gz'))
md_dti_img = nb.Nifti1Image(MD_DTI.astype(np.float32), dwi.get_affine()); nb.save(md_dti_img, os.path.join(args.output_dir, 'dti_md.nii.gz'))
l1_dti_img = nb.Nifti1Image(L1_DTI.astype(np.float32), dwi.get_affine()); nb.save(l1_dti_img, os.path.join(args.output_dir, 'dti_l1.nii.gz'))
lt_dti_img = nb.Nifti1Image(LT_DTI.astype(np.float32), dwi.get_affine()); nb.save(lt_dti_img, os.path.join(args.output_dir, 'dti_lt.nii.gz'))

evals_dti_img = nb.Nifti1Image(tenfit.evals.astype(np.float32), dwi.get_affine()); nb.save(evals_dti_img, os.path.join(args.output_dir, 'dti_evals.nii.gz'))
evecs_dti_img = nb.Nifti1Image(tenfit.evecs.astype(np.float32), dwi.get_affine()); nb.save(evecs_dti_img, os.path.join(args.output_dir, 'dti_evecs.nii.gz'))

# FWDTI fitting
print('computing FW-DTI tensor')

#fwtenmodel = fwdti.FreeWaterTensorModel(gtab,'NLLS')
if args.min_signal:
  print('using min_signal=%f' % args.min_signal)
  fwtenmodel = fwdti.FreeWaterTensorModel(gtab,'WLS', min_signal=args.min_signal)
else:
  fwtenmodel = fwdti.FreeWaterTensorModel(gtab,'WLS')

fwtenfit = fwtenmodel.fit(dwi.get_data(), mask.get_data())

print('computing anisotropy measures')
FA_FWDTI = dti.fractional_anisotropy(fwtenfit.evals)
FA_FWDTI[np.isnan(FA_FWDTI)] = 0
MD_FWDTI = dti.mean_diffusivity(fwtenfit.evals)
L1_FWDTI = dti.axial_diffusivity(fwtenfit.evals)
LT_FWDTI = dti.radial_diffusivity(fwtenfit.evals)

fa_fwdti_img = nb.Nifti1Image(FA_FWDTI.astype(np.float32), dwi.get_affine()); nb.save(fa_fwdti_img, os.path.join(args.output_dir, 'fwdti_fa.nii.gz'))
md_fwdti_img = nb.Nifti1Image(MD_FWDTI.astype(np.float32), dwi.get_affine()); nb.save(md_fwdti_img, os.path.join(args.output_dir, 'fwdti_md.nii.gz'))
l1_fwdti_img = nb.Nifti1Image(L1_FWDTI.astype(np.float32), dwi.get_affine()); nb.save(l1_fwdti_img, os.path.join(args.output_dir, 'fwdti_l1.nii.gz'))
lt_fwdti_img = nb.Nifti1Image(LT_FWDTI.astype(np.float32), dwi.get_affine()); nb.save(lt_fwdti_img, os.path.join(args.output_dir, 'fwdti_lt.nii.gz'))

f_fwdti_img = nb.Nifti1Image(fwtenfit.f.astype(np.float32), dwi.get_affine()); nb.save(f_fwdti_img,  os.path.join(args.output_dir, 'fwdti_f.nii.gz'))
evals_fwdti_img = nb.Nifti1Image(fwtenfit.evals.astype(np.float32), dwi.get_affine()); nb.save(evals_fwdti_img, os.path.join(args.output_dir, 'fwdti_evals.nii.gz'))
evecs_fwdti_img = nb.Nifti1Image(fwtenfit.evecs.astype(np.float32), dwi.get_affine()); nb.save(evecs_fwdti_img, os.path.join(args.output_dir, 'fwdti_evecs.nii.gz'))

#now visualize the DTI
#print('computing visualization')
#FA_DTI = np.clip(FA_DTI, 0, 1)
#RGB_DTI = color_fa(FA_DTI, DTItenfit.evecs)
#pl.imshow(RGB_DTI[:,:,slice])
#fig=pl.gcf()
#fig.savefig(os.path.join(args.output_dir, 'RGB_FA_DTI.png'))
#sphere = get_sphere('symmetric724')
#ren = fvtk.ren()
#cfa = RGB_DTI/RGB_DTI.max()
#fvtk.add(ren, fvtk.tensor(DTItenfit.evals[:,:,slice], DTItenfit.evecs[:,:,slice], cfa[:,:,slice], sphere))
#print('writing DTI image')
#fvtk.record(ren, n_frames=1, out_path='tensor_ellipsoids_DTI.png', size=(1200,1200))
#fvtk.clear(ren)

#now visualize the FW-DTI
#print('computing visualization')
#FA_FWDTI = np.clip(FA_FWDTI, 0, 1)
#RGB_FWDTI = color_fa(FA_FWDTI, FWDTItenfit.evecs)
#pl.imshow(RGB_FWDTI[:,:,slice])
#fig=pl.gcf()
#fig.savefig(os.path.join(args.output_dir, 'RGB_FA_FWDTI.png'))
#pl.imshow(FWDTItenfit.f[:,:,slice])
#pl.colorbar()
#fig=pl.gcf()
#fig.savefig(os.path.join(args.output_dir, 'f_FWDTI.png'))
#sphere = get_sphere('symmetric724')
#ren = fvtk.ren()
#cfa = RGB_DTI/RGB_DTI.max()
#fvtk.add(ren, fvtk.tensor(DTItenfit.evals[:,:,slice], DTItenfit.evecs[:,:,slice], cfa[:,:,slice], sphere))
#print('writing DTI image')
#fvtk.record(ren, n_frames=1, out_path='tensor_ellipsoids_FWDTI.png', size=(1200,1200))
#fvtk.clear(ren)

