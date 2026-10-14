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
====================================
rsfMRI: Compute Group-Level ICA
====================================


A preprocessing workflow for NCANDA resting state data.

This workflow makes use of:

- Nipype
- Nibabel

For example::

  python rsfmri_group_melodic.py -b /path/to/bold.nii.gz


This workflow takes an list of cleaned timeseries in standard space and
computes the group ICA Map.

"""

import os
import sys
import nipype.interfaces.fsl as fsl


def compute_group_ica(bold_filenames, bg_image, mask, output_dir, verbose):
    """
    Computes the group ICA from a list of scans in standard space.

    :param bold_filenames:
    :return results:
    """
    melodic = fsl.MELODIC()
    melodic.inputs.in_files = bold_filenames
    melodic.inputs.approach = 'concat'
    melodic.inputs.no_bet = True
    #melodic.inputs.bg_threshold = 0
    melodic.inputs.tr_sec = 2.2
    melodic.inputs.mm_thresh = .5
    melodic.inputs.out_stats = True
    melodic.inputs.out_dir = output_dir
    melodic.bg_image = bg_image
    #melodic.inputs.no_mask = True
    melodic.inputs.report = True
    melodic.inputs.mask = mask
    if verbose:
        print(melodic.inputs)
    result = melodic.run()
    return result


def main(args=None):
    print(args)
    if args:
        #bold_filenames = [os.path.join(args.cases_dir, scan) for scan in args.bold_scans]
        bold_filenames = [os.path.join(args.cases_dir, scan.strip(), 'standard/baseline/restingstate/reslice/sri24_2mm/warp/bold_noIntenCorr_4d_filtermotart_cleaned_bp_smooth_stripped.nii.gz') for scan in open(args.bold_scans).readlines()]
        bg_image = os.path.abspath(args.bg_image)
        mask = os.path.abspath(args.mask)
        output_dir = os.path.abspath(args.output_dir)
        verbose = args.verbose
        result = compute_group_ica(bold_filenames, bg_image, mask, output_dir, verbose)
        if args.verbose:
            print(result.outputs)
    else:
        print("You must specify args.")


if __name__ == "__main__":
    from argparse import ArgumentParser, RawTextHelpFormatter
    defstr = ' (default %(default)s)'
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-c", "--cases_dir", dest="cases_dir", 
                        help="NCANDA cases directory",
                        required=True)
    parser.add_argument("-b", "--bold_scans", dest="bold_scans",
                        help="NCANDA path to bold scans from cases", required=True)
    parser.add_argument("-t", "--bg_image", dest="bg_image",
                        help="NCANDA path to background image", required=True)
    parser.add_argument("-m", "--mask", dest="mask",
                        help="NCANDA path to mask image", required=True)
    parser.add_argument("--TR", dest="TR", default=None, type=float,
                        help="TR in seconds")
    parser.add_argument("-o", "--output_dir", dest="output_dir",
                        help="Output directory", required=True)
    parser.add_argument("-v", "--verbose", dest="verbose",
                        help="Turn on verbose", action='store_true')
    args = parser.parse_args()

    sys.exit(main(args=args))
