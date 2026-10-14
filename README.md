# NCANDA image processing pipelines

Structural, FreeSurfer, diffusion and resting-state MRI processing pipelines developed for the
National Consortium on Alcohol and NeuroDevelopment in Adolescence (NCANDA). This is the public
release of the scripts the NCANDA data core uses, published so other groups can process their own
data the same way.

The pipelines were built around the NCANDA acquisition protocol and directory layout. Data that
follows the same layout will run as is; different sequences may need changes to the templates.

## Contents

| Path | Contents |
|---|---|
| `templates/` | Sources for the pipeline scripts (`*.in`). CMake generates the runnable scripts in `bin/` from these. |
| `utils/` | Helper scripts used by the pipelines: QC images, statistics, CSV summaries |
| `rsfmri_tools/` | Resting-state fMRI modules and scripts |
| `data/` | Atlases and reference data used by the pipelines (see [Reference data](#reference-data)) |
| `CMakeLists.txt`, `CMakePresets.json` | Generate `bin/` from `templates/` |

## Requirements

- Linux with bash, Git LFS (the images in `data/` are stored in LFS), and CMake 3.21 or newer.
- The neuroimaging tools below. CMake records where each one lives; the `docker` preset in
  `CMakePresets.json` shows the layout the pipelines were developed with.

  | Tool | CMake variable |
  |---|---|
  | AFNI | `NCANDA_AFNI_DIR` |
  | ANTs | `NCANDA_ANTS_DIR` |
  | Convert3D | `NCANDA_C3D_DIR` |
  | Camino | `NCANDA_CAMINO_DIR` |
  | CMTK | `NCANDA_CMTKDIR` |
  | FreeSurfer | `NCANDA_FREESURFER_HOME` |
  | FSL | `NCANDA_FSLDIR` |
  | LWDP | `NCANDA_LWDP_DIR` |
  | naonlm3d | `NCANDA_NAONLM_DIR` |
  | Python environment | `NCANDA_PYTHON_DIR` |
  | ROBEX | `NCANDA_ROBEX_DIR` |
  | 3D Slicer CLI modules | `NCANDA_SLICER_CLI_DIR` |
  | Connectome Workbench | `NCANDA_CARET7_DIR` |

- Your own FreeSurfer license (free from the FreeSurfer website), installed where FreeSurfer expects
  it. No license is included here.
- Python 2 for two utilities, `utils/rsFMRI_artifact_detection` and
  `utils/dti_compute_motion_statistics.py`.

The simplest way to get all of the tools at the expected paths is the sibis-image-processing
container ([sibis-image-processing-public](https://github.com/sibis-platform/sibis-image-processing-public)).

## Getting started

1. Clone with LFS so the images download:

```bash
   git lfs install
   git clone https://github.com/sibis-platform/ncanda-image-processing-scripts-public.git
   cd ncanda-image-processing-scripts-public
```

2. Get the reference data that is not distributed here:

```bash
   bash data/fetch_external.sh
```

   It downloads the HCP Pipelines templates and prints instructions for the files you need to
   download yourself. See [Reference data](#reference-data).

3. Generate the pipeline scripts into `bin/`. Inside the container:

```bash
   cmake --preset docker .
```

   If your tools live elsewhere, add a `CMakeUserPresets.json` with a preset that inherits `docker`
   and overrides the `NCANDA_*` paths, or pass each one with `-D`. Rerun CMake after editing a
   template. If a configure run fails, delete `CMakeCache.txt` and `CMakeFiles/` before retrying.

## Preparing your data

The pipelines expect one directory per visit:

```
<cases>/
  NCANDA_S#####/                 subject: "NCANDA_S" followed by five digits
    <arm>/                       any name; NCANDA uses "standard"
      baseline/                  first visit, must be named "baseline"
        measures/demographics.csv
        structural/native/t1.nii.gz
        structural/native/t2.nii.gz
        diffusion/...
        restingstate/...
      <later visit>/             e.g. followup_1y
        ...
```

- **Subject directories must be named `NCANDA_S` plus five digits.** The setup script finds the
  subject, arm and visit by that pattern. Use it as a label for your own IDs.
- **Every visit needs `measures/demographics.csv`.** The pipelines read the scanner site code from
  column 4 of its last row, and a later visit's site must match baseline's. Site codes `A` and `D`
  switch on NCANDA's GE/Siemens diffusion harmonization, so use any other code for your own data.
- **Inputs.** Structural inputs are `structural/native/t1.nii.gz` and `t2.nii.gz`. The diffusion
  and resting-state inputs are read near the top of `ncanda_diffusion_pipeline.in` and
  `ncanda_restingstate_pipeline.in`.

## Running

From your cases directory:

```bash
<repo>/bin/ncanda_all_pipelines NCANDA_S#####/<arm>/baseline     # one visit
<repo>/bin/ncanda_all_visits NCANDA_S#####/<arm>                 # every visit of a subject
```

`ncanda_all_pipelines` runs the structural pipelines (including FreeSurfer), then diffusion, then
resting state. Each pipeline can also be run on its own:

| Area | Scripts |
|---|---|
| Structural | `ncanda_structural_pipeline`, `ncanda_structural_all_pipelines`, `ncanda_structural_cerebellum_pipeline`, `ncanda_structural_reformat_to_template` |
| FreeSurfer | `ncanda_freesurfer_pipeline`, `ncanda_freesurfer_longitudinal_pipeline`, `ncanda_freesurfer_post_pipeline` |
| Diffusion | `ncanda_diffusion_pipeline`, `ncanda_diffusion_post_pipeline`, `ncanda_diffusion_freewater_pipeline`, `correct_dwi_distortion_and_motion`, `correct_dwi_distortion_and_motion_2shell` |
| Resting state | `ncanda_restingstate_pipeline`, `ncanda_restingstate_longitudinal_pipeline`, `ncanda_restingstate_post_pipeline`, `check_restingstate_output` |
| Field maps | `ncanda_epi_unwarp_siemens` |
| QC images | `create_qc_image`, `create_qc_images_all_visits`, `create_qc_longitudinal_images` |

Each step checks whether its outputs are older than its inputs and only reruns what changed, so a
pipeline can be rerun safely. A file placed at the matching path under a `manual/` directory
overrides the generated one.

## Reference data

**Included in this repository**

| Path | Contents |
|---|---|
| `data/sri24/` | SRI24 atlas, plus parcellations, fiber masks and ROIs NCANDA derived from it |
| `data/freesurfer/` | Lookup tables and CSV templates for FreeSurfer measures |
| `data/hcp/templates/MNI152_T1_*_brain_compact*.nii.gz` | Compact MNI152 brain masks made by NCANDA |
| `data/hcp/templates/freesurfer/aparc*.32k_fs_LR.dlabel.nii` | FreeSurfer aparc and aparc.a2009s labels on the 32k_fs_LR mesh, made by NCANDA from the MNI152 template |
| `data/tbss/sri_cingulum.nii.gz` | Cingulum mask for TBSS |
| `data/restingstate/rs_qa_datadict.csv` | Resting-state QA data dictionary |
| `data/tbss/pepolar/ncanda_baseline_meet_criteria/` | NCANDA baseline TBSS template: group mean FA and skeleton masks |
| `data/restingstate/melodic/` | NCANDA group ICA: 25 component maps and `melodic_IC.nii.gz`, used for dual regression |
| `data/dti_mfc_correction/` | NCANDA GE/Siemens human phantom correction maps, applied to sites `A` and `D` only |
| `data/suit/` | SUIT cerebellar atlas and templates (Diedrichsen lab), plus files NCANDA derived from them |
| `data/autoptx/` | autoPtx tract protocols and structure lists |
| `data/mni/avg152T1_mask.nii.gz` | MNI avg152 T1 brain mask |

**Not included.** Third-party files come from their original sources under their own terms. Steps
marked *skipped* print an INFO message and continue when their file is missing.

| Path under `data/` | Source | Used by | If missing |
|---|---|---|---|
| `hcp/templates/MNI152_T1_1mm.nii.gz`, `MNI152_T1_2mm.nii.gz`, `standard_mesh_atlases/`, `91282_Greyordinates/`; `hcp/config/FreeSurferAllLut.txt`, `FreeSurferSubcorticalLabelTableLut.txt` | HCP Pipelines, via `fetch_external.sh` | FreeSurfer post, diffusion post, resting-state post | required |
| `hcp/templates/MMP_1.0/Q1-Q6_RelatedParcellation210.CorticalAreas_dil_Final_Final_Areas_Group_Colors.32k_fs_LR.dlabel.nii` | BALSA (Glasser et al. 2016), after accepting the HCP data use terms | MMP1.0 resting-state parcellation | skipped |
| `sri24/sri24_t1_div_t2_HCP1200.nii.gz`, `suit/SUIT_t1_div_t2_HCP1200.nii.gz` | derived from the HCP S1200 group average; not distributed | T1w/T2w bias correction | skipped |

## Differences from the NCANDA internal version

- Uploads to NCANDA's XNAT and REDCap servers are removed. Hooks that upload manual edits run only
  when the internal upload script is installed, so they do nothing here.
- Steps whose reference data is not distributed skip instead of failing.
- Example paths and IDs in comments are placeholders.

## Versions

Releases are tagged `vYYYY.MM.N`, matching the NCANDA internal release they were exported from.

## Citing

If you use these pipelines, please cite the NCANDA study and the papers describing the processing:

- Brown SA, et al. The National Consortium on Alcohol and NeuroDevelopment in Adolescence (NCANDA):
  a multisite study of adolescent development and substance use. *J Stud Alcohol Drugs*.
  2015;76(6):895-908.
- **Segmentations (structural, diffusion and resting-state pipelines):** Pfefferbaum A, Kwon D,
  Brumback T, et al. Altered brain developmental trajectories in adolescents after initiating
  drinking. *Am J Psychiatry*. 2018;175(4):370-380.
- **Diffusion measurements:** Pohl KM, Sullivan EV, Rohlfing T, et al. Harmonizing DTI measurements
  across scanners to examine the development of white matter microstructure in 803 adolescents of
  the NCANDA study. *NeuroImage*. 2016;130:194-213. doi:10.1016/j.neuroimage.2016.01.061
- **Resting-state processing:** Zhao Q, Kwon D, Müller-Oehring EM, et al. Longitudinally consistent
  estimates of intrinsic functional networks. *Hum Brain Mapp*. 2019;40(8):2511-2528.

Please also cite the tools and atlases you use, per their own instructions.

## License

- **Code:** BSD 3-Clause, Copyright SRI International and Stanford University. See [`COPYING`](COPYING).
- **`data/sri24/`:** Creative Commons Attribution-ShareAlike 3.0. See
  [`data/sri24/LICENSE`](data/sri24/LICENSE). The parcellations, fiber masks and ROIs in
  `data/sri24/` were created by NCANDA from the SRI24 atlas; they are modified from the original
  work and distributed under the same license.
- **`data/suit/`:** SUIT cerebellar atlas and templates by the Diedrichsen lab, with files NCANDA
  derived from them. Please cite SUIT per its documentation.
- **MNI-derived files** (`data/mni/`, compact MNI152 masks, aparc labels): from or derived from the MNI avg152 and ICBM152 templates, Montreal Neurological Institute, McGill University.
- **`data/autoptx/`:** tract protocols from autoPtx (de Groot et al.), distributed with attribution. Please cite autoPtx per its documentation.
- **Downloaded reference data:** each source's own terms apply.

## Support

Please report problems through GitHub issues. The pipelines are maintained by the NCANDA data core
at the Computational Neuroscience Laboratory, Stanford University, on a best-effort basis.
