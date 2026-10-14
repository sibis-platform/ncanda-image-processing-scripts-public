c3d sri24_parc116.nii.gz -replace 131 0 132 0 133 0 134 0 -o /tmp/blub.nii.gz
fslmaths ../sri24_tissues.nii.gz -thr 2 -uthr 2 -bin -mul /tmp/blub.nii.gz sri24_parc116_gm.nii.gz
