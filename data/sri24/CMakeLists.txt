
##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
##  $HeadURL$
##  $Revision$
##  $LastChangedDate$
##  $LastChangedBy$
##

FILE(GLOB files "${CMAKE_CURRENT_SOURCE_DIR}/*.nii.gz")
INSTALL(FILES LICENSE ${files} DESTINATION ${CMTK_INSTALL_DATA_DIR}/sri24 COMPONENT runtime)

FILE(GLOB files_parc "${CMAKE_CURRENT_SOURCE_DIR}/parcellation/*.nii.gz")
INSTALL(FILES ${files_parc} DESTINATION ${CMTK_INSTALL_DATA_DIR}/sri24/parcellation COMPONENT runtime)

FILE(GLOB files_parc "${CMAKE_CURRENT_SOURCE_DIR}/fiber_masks/*.nii.gz")
INSTALL(FILES ${files_parc} DESTINATION ${CMTK_INSTALL_DATA_DIR}/sri24/fiber_masks COMPONENT runtime)
