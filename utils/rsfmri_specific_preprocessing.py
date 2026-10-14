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
=====================
rsfMRI: FSL, aCompCor
=====================


A preprocessing workflow for NCANDA resting state data.

This workflow makes use of:

- FSL
- Nibabel
- aCompCor

For example::

  python rsfmri_preprocessing.py -c cases -a standard -v baseline -s <subject> -t 2.2


This workflow takes an unaarped and motion corrected resting timeseries and
preprocesses it to produce timeseries coordinates or grayordinates.

"""
import os
import sys

import numpy as np
import scipy as sp
import matplotlib
# disable warnings
matplotlib.use('AGG')

from scipy.special import legendre

import nipype
crashDir=os.getenv('NIPYPE_CRASH_DIR')
if crashDir:
  nipype.config.set("execution", "crashdump_dir", crashDir)

import nibabel as nb
from nipype import Workflow, Node, MapNode
from nipype.interfaces import fsl, Function
from nipype.interfaces.base import CommandLine
from nipype.algorithms.rapidart import ArtifactDetect
from nipype.interfaces.io import DataSink
from nipype.interfaces.utility import IdentityInterface
from nipype.utils.filemanip import (filename_to_list,
                                    list_to_filename,
                                    split_filename)

CommandLine.set_default_terminal_output('allatonce')
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

imports = ['import os',
           'import nibabel as nb',
           'import numpy as np',
           'import scipy as sp',
           'from nipype.utils.filemanip import filename_to_list, list_to_filename, split_filename',
           'from scipy.special import legendre'
           ]


def bandpass_filter(files, lowpass_freq, highpass_freq, tr):
    """Bandpass filter the input files

    Parameters
    ----------
    files: list of 4d nifti files
    lowpass_freq: cutoff frequency for the low pass filter (in Hz)
    highpass_freq: cutoff frequency for the high pass filter (in Hz)
    tr: repetition time in seconds, used to compute sampling rate (in Hz)
    """
    fs = 1./tr
    out_files = []
    for filename in filename_to_list(files):
        path, name, ext = split_filename(filename)
        out_file = os.path.join(os.getcwd(), name + '_bp' + ext)
        img = nb.load(filename)
        timepoints = img.shape[-1]
        F = np.zeros(timepoints)
        lowidx = timepoints/2 + 1
        if lowpass_freq > 0:
            lowidx = np.round(float(lowpass_freq) / fs * timepoints)
        highidx = 0
        if highpass_freq > 0:
            highidx = np.round(float(highpass_freq) / fs * timepoints)
        F[int(highidx):int(lowidx)] = 1
        F = ((F + F[::-1]) > 0).astype(int)

        # 05/18/26: Updating outdated nibabel calls
        # data = img.get_data()
        # if np.all(F == 1):
        #     filtered_data = data
        # else:
        #     filtered_data = np.real(np.fft.ifftn(np.fft.fftn(data) * F))
        # img_out = nb.Nifti1Image(filtered_data, img.get_affine(),img.get_header())
        # img_out.to_filename(out_file)
        data = np.asanyarray(img.dataobj)
        if np.all(F == 1):
            filtered_data = data
        else:
            filtered_data = np.real(np.fft.ifftn(np.fft.fftn(data) * F))

        img_out = nb.Nifti1Image(filtered_data, img.affine, img.header)
        img_out.to_filename(out_file)
        out_files.append(out_file)
    return list_to_filename(out_files)


def motion_regressors(motion_params, order=0, derivatives=1):
    """Compute motion regressors upto given order and derivative

    motion + d(motion)/dt + d2(motion)/dt2 (linear + quadratic)
    """
    out_files = []
    for idx, filename in enumerate(filename_to_list(motion_params)):
        params = np.genfromtxt(filename)
        out_params = params
        for d in range(1, derivatives + 1):
            cparams = np.vstack((np.repeat(params[0, :][None, :], d, axis=0),
                                 params))
            out_params = np.hstack((out_params, np.diff(cparams, d, axis=0)))
        out_params2 = out_params
        for i in range(2, order + 1):
            out_params2 = np.hstack((out_params2, np.power(out_params, i)))
        filename = os.path.join(os.getcwd(), "motion_regressor%02d.txt" % idx)
        np.savetxt(filename, out_params2, fmt="%.10f")
        out_files.append(filename)
    return out_files


def build_motion_filter(motion_params, comp_norm, outliers, detrend_poly=None):
    """Builds a regressor set comprisong motion parameters, composite norm and
    outliers

    The outliers are added as a single time point column for each outlier


    Parameters
    ----------

    motion_params: a text file containing motion parameters and its derivatives
    comp_norm: a text file containing the composite norm
    outliers: a text file containing 0-based outlier indices
    detrend_poly: number of polynomials to add to detrend

    Returns
    -------
    components_file: a text file containing all the regressors
    """
    out_files = []
    for idx, filename in enumerate(filename_to_list(motion_params)):
        params = np.genfromtxt(filename)
        norm_val = np.genfromtxt(filename_to_list(comp_norm)[int(idx)])
        out_params = np.hstack((params, norm_val[:, None]))
        try:
            outlier_val = np.genfromtxt(filename_to_list(outliers)[int(idx)])
        except IOError:
            outlier_val = np.empty(0)
        for index in np.atleast_1d(outlier_val):
            outlier_vector = np.zeros((out_params.shape[0], 1))
            outlier_vector[int(index)] = 1
            out_params = np.hstack((out_params, outlier_vector))
        if detrend_poly:
            timepoints = out_params.shape[0]
            X = np.ones((timepoints, 1))
            for i in range(detrend_poly):
                X = np.hstack((X, legendre(
                    i + 1)(np.linspace(-1, 1, timepoints))[:, None]))
            out_params = np.hstack((out_params, X))
        filename = os.path.join(os.getcwd(), "filter_regressor%02d.txt" % idx)
        np.savetxt(filename, out_params, fmt="%.10f")
        out_files.append(filename)
    return out_files


def extract_noise_components(realigned_file, mask_file, num_components=5,
                             extra_regressors=None):
    """Derive components most reflective of physiological noise

    Parameters
    ----------
    realigned_file: a 4D Nifti file containing realigned volumes
    mask_file: a 3D Nifti file containing white matter + ventricular masks
    num_components: number of components to use for noise decomposition
    extra_regressors: additional regressors to add

    Returns
    -------
    components_file: a text file containing the noise components
    """
    imgseries = nb.load(realigned_file)
    components = None
    for filename in filename_to_list(mask_file):
        # mask = nb.load(filename).get_data()   # 05/18/26: Updated to newer call
        mask = np.asanyarray(nb.load(filename).dataobj)
        if len(np.nonzero(mask > 0)[0]) == 0:
            continue
        # voxel_timecourses = imgseries.get_data()[mask > 0] # 05/18/26: Updated to newer call
        voxel_timecourses = np.asanyarray(imgseries.dataobj)[mask > 0] 
        voxel_timecourses[np.isnan(np.sum(voxel_timecourses, axis=1)), :] = 0
        # remove mean and normalize by variance
        # voxel_timecourses.shape == [nvoxels, time]
        X = voxel_timecourses.T
        stdX = np.std(X, axis=0)
        stdX[stdX == 0] = 1.
        stdX[np.isnan(stdX)] = 1.
        stdX[np.isinf(stdX)] = 1.
        X = (X - np.mean(X, axis=0))/stdX
        u, _, _ = sp.linalg.svd(X, full_matrices=False)
        if components is None:
            components = u[:, :num_components]
        else:
            components = np.hstack((components, u[:, :num_components]))
    if extra_regressors:
        regressors = np.genfromtxt(extra_regressors)
        components = np.hstack((components, regressors))
    components_file = os.path.join(os.getcwd(), 'noise_components.txt')
    np.savetxt(components_file, components, fmt="%.10f")
    return components_file


def rename(in_files, suffix=None):
    from nipype.utils.filemanip import (filename_to_list, split_filename,
                                        list_to_filename)
    out_files = []
    for idx, filename in enumerate(filename_to_list(in_files)):
        _, name, ext = split_filename(filename)
        if suffix is None:
            out_files.append(name + ('_%03d' % idx) + ext)
        else:
            out_files.append(name + suffix + ext)
    return list_to_filename(out_files)


def create_rest_workflow(name='resting'):
    """
    Creates the preprocessing workflow
    """
    wf = Workflow(name=name)

    # Get the input files from motion correction etc.
    input_node = Node(interface=IdentityInterface(fields=['bold_unwarped',
                                                          'motion_params',
                                                          'brain_mask',
                                                          'norm_threshold',
                                                          'wm_vent_mask',
                                                          'tr',
                                                          'num_components',
                                                          #'vol_fwhm',
                                                          'lowpass_freq',
                                                          'highpass_freq',
                                                          'z_threshold']),
                      name='input_spec')
    # define the node to gather all the outputs
    output_node = Node(interface=IdentityInterface(fields=['motion_params',
                                                           'motion_plots',
                                                           'norm_files',
                                                           'intensity_files',
                                                           'outlier_files',
                                                           'brain_mask',
                                                           'mc_out_f',
                                                           'mc_out_pf',
                                                           'cc_out_f',
                                                           'cc_out_pf',
                                                           'bandpassed',
                                                           #'smoothed',
                                                           'motion_regressors',
                                                           'compcorr_regressors']),
                       name='output_spec')

    """Use :class:`nipype.algorithms.rapidart` to determine which of the
    images in the functional series are outliers based on deviations in
    intensity or movement.
    """

    art = Node(interface=ArtifactDetect(), name="art")
    art.inputs.use_differences = [True, False]
    art.inputs.mask_type = 'file'
    art.inputs.parameter_source = 'FSL'
    art.inputs.bound_by_brainmask = False

    """Here we are connecting all the nodes together. Notice that we add the merge node only if you choose
    to use 4D. Also `get_vox_dims` function is passed along the input volume of normalise to set the optimal
    voxel sizes.
    """

    wf.connect(input_node, 'bold_unwarped', art, 'realigned_files')
    wf.connect(input_node, 'motion_params', art, 'realignment_parameters')
    wf.connect(input_node, 'brain_mask', art, 'mask_file')
    wf.connect(input_node, 'norm_threshold', art, 'norm_threshold')
    wf.connect(input_node, 'z_threshold', art, 'zintensity_threshold')

    # Compute motion regressors
    motreg = Node(Function(input_names=['motion_params', 'order',
                                        'derivatives'],
                           output_names=['out_files'],
                           function=motion_regressors,
                           imports=imports),
                  name='getmotionregress')
    wf.connect(input_node, 'motion_params', motreg, 'motion_params')

    # Create a filter to remove motion and art confounds
    create_motion_filter = Node(Function(input_names=['motion_params',
                                                      'comp_norm',
                                                      'outliers',
                                                      'detrend_poly'],
                                         output_names=['out_files'],
                                         function=build_motion_filter,
                                         imports=imports),
                                name='makemotionbasedfilter')
    create_motion_filter.inputs.detrend_poly = 2
    wf.connect(motreg, 'out_files', create_motion_filter, 'motion_params')
    wf.connect(art, 'norm_files', create_motion_filter, 'comp_norm')
    wf.connect(art, 'outlier_files', create_motion_filter, 'outliers')

    motion_filter = MapNode(fsl.GLM(out_f_name='F_mcart.nii.gz',
                                    out_pf_name='pF_mcart.nii.gz',
                                    demean=True),
                            iterfield=['in_file', 'design', 'out_res_name'],
                            name='filtermotion')

    wf.connect(input_node, 'bold_unwarped', motion_filter, 'in_file')
    wf.connect(input_node, ('bold_unwarped', rename, '_filtermotart'), motion_filter, 'out_res_name')
    wf.connect(create_motion_filter, 'out_files', motion_filter, 'design')

    create_compcorr_filter = MapNode(Function(input_names=['realigned_file',
                                                           'mask_file',
                                                           'num_components',
                                                           'extra_regressors'],
                                     output_names=['out_files'],
                                     function=extract_noise_components,
                                     imports=imports),
                                     iterfield=['realigned_file', 'extra_regressors'],
                                     name='makecompcorrfilter')

    wf.connect(create_motion_filter, 'out_files', create_compcorr_filter, 'extra_regressors')
    wf.connect(motion_filter, 'out_res', create_compcorr_filter, 'realigned_file')
    wf.connect(input_node, 'wm_vent_mask', create_compcorr_filter, 'mask_file')
    wf.connect(input_node, 'num_components', create_compcorr_filter, 'num_components')

    compcorr_filter = MapNode(fsl.GLM(out_f_name='F.nii.gz',
                              out_pf_name='pF.nii.gz',
                              demean=True),
                              iterfield=['in_file', 'design', 'out_res_name'],
                              name='filter_noise_nosmooth')
    wf.connect(motion_filter, 'out_res', compcorr_filter, 'in_file')
    wf.connect(motion_filter, ('out_res', rename, '_cleaned'),
               compcorr_filter, 'out_res_name')
    wf.connect(create_compcorr_filter, 'out_files', compcorr_filter, 'design')
    wf.connect(input_node, 'brain_mask', compcorr_filter, 'mask')

    bandpass = Node(Function(input_names=['files', 'lowpass_freq',
                                          'highpass_freq', 'tr'],
                             output_names=['out_files'],
                             function=bandpass_filter,
                             imports=imports),
                    name='bandpass_unsmooth')

    wf.connect(compcorr_filter, 'out_res', bandpass, 'files')
    wf.connect(input_node, 'highpass_freq', bandpass, 'highpass_freq')
    wf.connect(input_node, 'lowpass_freq', bandpass, 'lowpass_freq')
    wf.connect(input_node, 'tr', bandpass, 'tr')

    #"""Smooth the functional data using
    #:class:`nipype.interfaces.fsl.IsotropicSmooth`.
    #"""

    #smooth = MapNode(interface=fsl.IsotropicSmooth(),
    #                 name="smooth",
    #                 iterfield=["in_file"])

    #wf.connect(input_node, 'vol_fwhm', smooth, 'fwhm')
    #wf.connect(bandpass, 'out_files', smooth, 'in_file')

    # Save the relevant data into an output_node
    wf.connect(input_node, 'motion_params', output_node, 'motion_params')
    wf.connect(art, 'norm_files', output_node, 'norm_files')
    wf.connect(art, 'intensity_files', output_node, 'intensity_files')
    wf.connect(art, 'outlier_files', output_node, 'outlier_files')
    wf.connect(art, 'plot_files', output_node, 'motion_plots')
    wf.connect(input_node, 'brain_mask', output_node, 'brain_mask')
    wf.connect(motion_filter, 'out_f', output_node, 'mc_out_f')
    wf.connect(motion_filter, 'out_pf', output_node, 'mc_out_pf')
    wf.connect(compcorr_filter, 'out_f', output_node, 'cc_out_f')
    wf.connect(compcorr_filter, 'out_pf', output_node, 'cc_out_pf')
    wf.connect(bandpass, 'out_files', output_node, 'bandpassed')
    #wf.connect(smooth, 'out_file', output_node, 'smoothed')
    wf.connect(create_motion_filter, 'out_files',
               output_node, 'motion_regressors')
    wf.connect(create_compcorr_filter, 'out_files',
               output_node, 'compcorr_regressors')
    
    return wf


"""
Creates the full workflow including getting information from dicom files
"""


def create_workflow(args, name=None):
    """
    Create the main workflow and configure parameters
    """
    if not name:
        name = 'rs_specific_processing_' + args.subject
    if args.prov:
        nipype.config.enable_provenance()
    if args.verbose:
        print("Starting nipype workflow...")

    # Create main resting state workflow
    wf = Workflow(name=name)

    # Create preprocessing workflow
    rest = create_rest_workflow(name='preprocess')

    # Define path variables
    cases_dir = os.path.abspath(args.cases_dir)
    subject = args.subject
    arm = args.arm
    visit = args.visit
    modality = "restingstate"

    # Set the base directory to access files
    rest_dir = os.path.join(cases_dir, subject, arm, visit, modality)

    # Configure workflow with input parameters
    inputs = rest.inputs.input_spec
    inputs.bold_unwarped = os.path.join(rest_dir, args.bold_unwarped)
    if not os.path.exists(inputs.bold_unwarped): 
      print("Error: %s does not exist ! Make sure --bold_unwarped is correctly defined!" % (inputs.bold_unwarped))
      sys.exit(1)

    inputs.motion_params = os.path.join(rest_dir, args.motion_params)
    if not os.path.exists(inputs.motion_params): 
      print("Error: %s does not exist ! Make sure --motion_params is correctly defined!" % (inputs.motion_params))
      sys.exit(1)

    inputs.brain_mask = os.path.join(rest_dir, args.brain_mask)
    if not os.path.exists(inputs.brain_mask): 
      print("Error: %s does not exist ! Make sure --brain_mask is correctly defined!" % (inputs.brain_mask))
      sys.exit(1)

    inputs.wm_vent_mask = os.path.join(rest_dir, args.wm_vent_mask)
    if not os.path.exists(inputs.wm_vent_mask): 
      print("Error: %s does not exist ! Make sure --wm_vent_mask is correctly defined!" % (inputs.wm_vent_mask))
      sys.exit(1)

    inputs.tr = args.tr
    #inputs.vol_fwhm = args.vol_fwhm
    inputs.norm_threshold = args.norm_threshold
    inputs.lowpass_freq = args.lowpass_freq
    inputs.highpass_freq = args.highpass_freq
    inputs.z_threshold = args.z_threshold

    # Add a datasink to define data outputs
    datasink = Node(interface=DataSink(), name="datasink")
    if args.output_dir:
        results_dir = os.path.abspath(args.output_dir)
    else:
        results_dir = rest_dir
    datasink.inputs.base_directory = results_dir
    datasink.inputs.container = "rs_specific_processing"
    wf.connect(rest, 'output_spec.norm_files', datasink, 'qa.art.@norm')
    wf.connect(rest, 'output_spec.motion_plots', datasink, 'qa.art.@plot')
    wf.connect(rest, 'output_spec.intensity_files', datasink, 'qa.art.@intensity')
    wf.connect(rest, 'output_spec.outlier_files', datasink, 'qa.art.@outlier_files')
    wf.connect(rest, 'output_spec.mc_out_f', datasink, 'qa.compmaps.@mc_F')
    wf.connect(rest, 'output_spec.mc_out_pf', datasink, 'qa.compmaps.@mc_pF')
    wf.connect(rest, 'output_spec.cc_out_f', datasink, 'qa.compmaps')
    wf.connect(rest, 'output_spec.cc_out_pf', datasink, 'qa.compmaps.@p')
    wf.connect(rest, 'output_spec.bandpassed', datasink, 'timeseries.@bandpassed')
    #wf.connect(rest, 'output_spec.smoothed', datasink, 'timeseries.@smoothed')
    wf.connect(rest, 'output_spec.motion_regressors',
               datasink, 'regressors.@motion')
    wf.connect(rest, 'output_spec.compcorr_regressors',
               datasink, 'regressors.@compcorr')
               
    return wf

if __name__ == "__main__":
    from argparse import ArgumentParser, RawTextHelpFormatter
    defstr = ' (default %(default)s)'
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-c", "--cases_dir", dest="cases_dir",
                        default=os.getcwd(),
                        help="NCANDA Cases Directory" + defstr)
    parser.add_argument("-s", "--subject", dest="subject",
                        help="NCANDA Subject Identifier", required=True)
    parser.add_argument("-a", "--arm", dest="arm",
                        help="NCANDA Study Arm", required=True)
    parser.add_argument("-v", "--visit", dest="visit",
                        help="NCANDA Visit", required=True)
    parser.add_argument("--bold_unwarped", dest="bold_unwarped",
                        help="Unwarped 4D BOLD series", default="bold/3_unwarped/bold_noIntenCorr_4d.nii.gz")
    parser.add_argument("--motion_params", dest="motion_params",
                        help="Motion parameters from FSl .par", default="bold/2_motion_corrected/bold_mcf.par")
    parser.add_argument("--brain_mask", dest="brain_mask",
                        help="Brain mask", default="reslice/bold_native/brainmask.nii.gz")
    parser.add_argument("--wm_vent_mask", dest="wm_vent_mask",
                        help="White matter and ventricle mask", default="reslice/bold_native/wm_ven_mask.nii.gz")
    parser.add_argument("-t", "--tr", dest="tr", default=None, type=float,
                        required=True, help="TR in seconds")
    #parser.add_argument('--vol_fwhm', default=6., dest='vol_fwhm', type=float,
    #                    help="Spatial Full Width Half Maximum (FWHM)" + defstr)
    parser.add_argument('-n', '--norm_threshold', dest='norm_threshold',
                        type=float, default=0.3,
                        help="Movement threshold used in artifact detection" + defstr)
    parser.add_argument('-z', '--z_threshold', dest='z_threshold',
                        type=float, default=5,
                        help="Z threshold used in artifact detection" + defstr)
    parser.add_argument("-l", "--lowpass_freq", dest="lowpass_freq",
                        default=0.1, help="Low pass frequency (Hz)" + defstr)
    parser.add_argument("-u", "--highpass_freq", dest="highpass_freq",
                        default=0.01, help="High pass frequency (Hz)" + defstr)
    parser.add_argument("-o", "--output_dir", dest="output_dir",
                        help="Output directory base")
    parser.add_argument("-w", "--work_dir", dest="work_dir",
                        help="Working directory base")
    parser.add_argument("-p", "--provenance", dest="prov",
                        help="Output provenance file", action='store_true')
    parser.add_argument("-m", "--multicore", dest='multicore', default='Linear',
                        help="Set to 'MultiProc' to use all cores")
    parser.add_argument("-g", "--graph", dest="graph",
                        help="Turn on writing a graph", action='store_true')
    parser.add_argument("-V", "--verbose", dest="verbose",
                        help="Turn on verbose", action='store_true')
    args = parser.parse_args()

    wf = create_workflow(args)

    if args.work_dir:
        work_dir = os.path.abspath(args.work_dir)
    else:
        work_dir = os.getcwd()

    if args.verbose:
        nipype.config.enable_debug_mode()
        nipype.logging.update_logging(nipype.config)

    wf.base_dir = work_dir
    if args.graph:
        wf.write_graph(graph2use='colored')
    wf.run(plugin=args.multicore)

