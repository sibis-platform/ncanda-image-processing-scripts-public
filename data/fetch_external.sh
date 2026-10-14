#!/bin/bash
# Fetch reference data that this repository does not redistribute.
# Run once after cloning:  bash data/fetch_external.sh
# Override the HCP Pipelines release with:  HCP_TAG=vX.Y.Z bash data/fetch_external.sh
set -euo pipefail

DATA_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
HCP_TAG=${HCP_TAG:-v3.21.0}
HCP_URL="https://github.com/Washington-University/HCPpipelines/archive/refs/tags/${HCP_TAG}.tar.gz"

# HCP Pipelines path : path under data/
HCP_FILES=(
  "global/templates/MNI152_T1_1mm.nii.gz:hcp/templates/MNI152_T1_1mm.nii.gz"
  "global/templates/MNI152_T1_2mm.nii.gz:hcp/templates/MNI152_T1_2mm.nii.gz"
  "global/templates/standard_mesh_atlases:hcp/templates/standard_mesh_atlases"
  "global/templates/91282_Greyordinates:hcp/templates/91282_Greyordinates"
  "global/config/FreeSurferAllLut.txt:hcp/config/FreeSurferAllLut.txt"
  "global/config/FreeSurferSubcorticalLabelTableLut.txt:hcp/config/FreeSurferSubcorticalLabelTableLut.txt"
)

hcp_complete() {
  for m in "${HCP_FILES[@]}"; do [ -e "${DATA_DIR}/${m#*:}" ] || return 1; done
}

if hcp_complete; then
  echo "HCP Pipelines templates already present, skipping download."
else
  command -v curl >/dev/null || { echo "ERROR: curl is required"; exit 1; }
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  echo "Downloading HCP Pipelines ${HCP_TAG} ..."
  curl -fL --retry 3 -o "${tmp}/hcp.tar.gz" "${HCP_URL}"
  tar -xzf "${tmp}/hcp.tar.gz" -C "$tmp" --wildcards '*/global/templates/*' '*/global/config/*'
  src_root=$(find "$tmp" -mindepth 1 -maxdepth 1 -type d | head -1)
  for m in "${HCP_FILES[@]}"; do
    src="${src_root}/${m%%:*}"; dst="${DATA_DIR}/${m#*:}"
    [ -e "$src" ] || { echo "ERROR: ${m%%:*} not found in HCP Pipelines ${HCP_TAG}"; exit 1; }
    mkdir -p "$(dirname "$dst")"; rm -rf "$dst"; cp -a "$src" "$dst"
  done
  if grep -rlq 'git-lfs.github.com/spec' "${DATA_DIR}/hcp" 2>/dev/null; then
    echo "ERROR: downloaded files are Git LFS pointers, not data"; exit 1
  fi
  echo "HCP Pipelines templates installed."
fi

echo
echo "Reference data status:"
missing=0
report() {  # label  required|optional  used-by  source  paths...
  local label=$1 status=$2 used=$3 source=$4; shift 4
  local absent=()
  for p in "$@"; do [ -e "${DATA_DIR}/$p" ] || absent+=("$p"); done
  if [ ${#absent[@]} -eq 0 ]; then echo "OK        $label"; return; fi
  if [ "$status" = required ]; then missing=1; echo "MISSING   $label (required by $used)"
  else echo "OPTIONAL  $label (without it, $used is skipped)"; fi
  echo "          Source: $source"
  for p in "${absent[@]}"; do echo "          -> data/$p"; done
}

report "HCP Pipelines templates" required "FreeSurfer post, diffusion post and resting-state post" \
  "this script (HCP Pipelines ${HCP_TAG})" \
  hcp/templates/MNI152_T1_1mm.nii.gz hcp/templates/MNI152_T1_2mm.nii.gz \
  hcp/templates/standard_mesh_atlases hcp/templates/91282_Greyordinates \
  hcp/config/FreeSurferAllLut.txt hcp/config/FreeSurferSubcorticalLabelTableLut.txt

report "HCP-MMP1.0 cortical parcellation" optional "the MMP1.0 resting-state parcellation" \
  "BALSA study RVVG (Glasser et al. 2016), after accepting the HCP data use terms" \
  hcp/templates/MMP_1.0/Q1-Q6_RelatedParcellation210.CorticalAreas_dil_Final_Final_Areas_Group_Colors.32k_fs_LR.dlabel.nii

report "FreeSurfer labels on the 32k_fs_LR mesh" optional "the aparc resting-state parcellations" \
  "included in this repository" \
  hcp/templates/freesurfer/aparc.32k_fs_LR.dlabel.nii hcp/templates/freesurfer/aparc.a2009s.32k_fs_LR.dlabel.nii

report "autoPtx tract protocols" required "diffusion post tract measures" \
  "included in this repository" \
  autoptx/structureList autoptx/structureListLR autoptx/protocols

report "SUIT cerebellar atlas and templates" required "the cerebellum pipeline" \
  "included in this repository" \
  suit/SUIT_bias_corrected.nii.gz suit/SUIT_icbm_gm.nii.gz suit/SUIT_icbm_wm.nii.gz \
  suit/SUIT_icbm_csf.nii.gz suit/Cerebellum-SUIT.nii.gz suit/Cerebellum-SUIT.txt \
  suit/Cerebellum-SUIT_bin.nii.gz suit/Cerebellum-SUIT_bin.txt suit/SUIT_ribbon_50.nii.gz

report "MNI avg152 brain mask" required "the resting-state pipeline" \
  "included in this repository" \
  mni/avg152T1_mask.nii.gz

echo
if [ "$missing" -ne 0 ]; then
  echo "Some required data is missing: the pipelines named above will fail until it is in place."
  exit 1
fi
echo "All required reference data is in place."
