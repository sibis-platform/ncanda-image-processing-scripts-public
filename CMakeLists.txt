
##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
##  $HeadURL$
##  $Revision$
##  $LastChangedDate$
##  $LastChangedBy$
##

cmake_minimum_required(VERSION 2.8)

# set default build mode
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  message(STATUS "Setting build type to 'Debug' as none was specified.")
  set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Choose the type of build, options are: None(CMAKE_CXX_FLAGS or CMAKE_C_FLAGS used) Debug Release RelWithDebInfo MinSizeRel." FORCE)
  # Set the possible values of build type for cmake-gui
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()

project(NCANDA_PIPELINES)

set(NCANDA_CMTKDIR_HELP "Default value for CMTKDIR environment variable. This should be the directory that contains either the CMTK binaries or the 'cmtk' wrapper.")
set(NCANDA_FSLDIR_HELP "Default value for FSLDIR environment variable (this should be what FSL expects it to be)")
set(NCANDA_CAMINO_DIR_HELP "Default value for CAMINO_DIR environment variable (root of the CAMINO installation; binaries are expected in $CAMINO_DIR/bin/)")
set(NCANDA_ROBEX_DIR_HELP "Default value for ROBEX_DIR environment variable - this is where the ROBEX executable is found")
set(NCANDA_LWDP_DIR_HELP "Default value for LWDP_DIR environment variable - this should be the directory that contains lwdp.sh")
set(NCANDA_AFNI_DIR_HELP "Default value for AFNI_DIR environment variable - this should be the directory that contains the AFNI binaries")
set(NCANDA_ITKSNAP_HELP "Default value for ITKSNAP environment variable - this should be path to the ITK-SNAP binary executable")
set(NCANDA_FREESURFER_HOME_HELP "Default value for FREESURFER_HOME environment variable - this should be path to the FreeSurfer installation")
set(NCANDA_FREESURFER_QA_TOOLS_HELP "Default value for FREESURFER_QA_TOOLS environment variable - this should be path to the FreeSurfer_qa installation")
set(NCANDA_SLICER_CLI_DIR_HELP "Default value for SLICER_CLI environment variable - this should be path to the Slicer CLI directory, e.g. where IslandRemoval is located")
set(NCANDA_ANTS_DIR_HELP "Default value for ANTS_DIR environment variable - this should be the directory that contains the ANTS binaries")
set(NCANDA_C3D_DIR_HELP "Default value for C3D_DIR environment variable - this should be the directory that contains the C3D binaries")
set(NCANDA_NAONLM_DIR_HELP "Default value for NAONLM_DIR environment variable - this should be the directory that contains the NAONLM binaries")
set(NCANDA_PYTHON_DIR_HELP "Default value for PYTHON_DIR environment variable - this should be the directory that contains the Python binaries")
set(NCANDA_CARET7_DIR_HELP "Default value for CARET7_DIR environment variable - this should be the directory that contains the workbench binaries")
set(NCANDA_MSM_DIR_HELP "Default value for MSM_DIR environment variable - this should be the directory that contains the MSM binaries")

set(NCANDA_PIPEOP_EMAIL "NOTFOUND" CACHE STRING "eMail address of the pipeline operator. This is where messages about serious errors will be send. Separate multiple addresses with space.")
set(NCANDA_RSFMRI_DROPVOLUMES "5" CACHE STRING "Number of volumes to drop at the beginning of an rs-fMRI series to allow for global intensity fluctuation. Note, that the first file is always dropped by the artifact detection so set it to n-1.")

set(USE_ENVIRONMENT_MODULE TRUE CACHE BOOL "Using Environment Module")
if(USE_ENVIRONMENT_MODULE)
  set(MODULESHOME $ENV{MODULESHOME})
  if("${MODULESHOME}" STREQUAL "")
    message("Environment Module is not found.")
    set(USE_ENVIRONMENT_MODULE FALSE CACHE BOOL "Using Environment Module" FORCE)
  else()
    message("Environment Module is found.")
  endif()
endif()
if(USE_ENVIRONMENT_MODULE)
  #execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show cmtk/3.2.3 ERROR_VARIABLE ev)
  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show cmtk/r5433 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep CMTKDIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE CMTKDIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("CMTKDIR=${CMTKDIR}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show fsl/5.0.10 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep FSLDIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE FSLDIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("FSLDIR=${FSLDIR}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show camino/20150527 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep CAMINO_DIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE CAMINO_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("CAMINO_DIR=${CAMINO_DIR}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show robex/1.2 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep ROBEX_DIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE ROBEX_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("ROBEX_DIR=${ROBEX_DIR}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show lwdp/r19 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep LWDP_DIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE LWDP_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("LWDP_DIR=${LWDP_DIR}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show afni/20150519 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep AFNI_DIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE AFNI_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("AFNI_DIR=${AFNI_DIR}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show itksnap/2.4.0 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep ITKSNAP_DIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE ITKSNAP_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  if(NOT "${ITKSNAP_DIR}" STREQUAL "")
    set(ITKSNAP ${ITKSNAP_DIR}/bin/itksnap)
  endif()
  message("ITKSNAP=${ITKSNAP}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show freesurfer/5.3.0-hcp ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep FREESURFER_HOME COMMAND cut -d " " -f 3 OUTPUT_VARIABLE FREESURFER_HOME OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("FREESURFER_HOME=${FREESURFER_HOME}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show freesurfer_qa/QAtools_v1.2.patch ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep FREESURFER_QA_TOOLS COMMAND cut -d " " -f 3 OUTPUT_VARIABLE FREESURFER_QA_TOOLS OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("FREESURFER_QA_TOOLS=${FREESURFER_QA_TOOLS}")


  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show slicer/r24545 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep SLICER_CLI COMMAND cut -d " " -f 3 OUTPUT_VARIABLE SLICER_CLI OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("SLICER_CLI=${SLICER_CLI}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show ants/2.1.0 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep ANTS_DIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE ANTS_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("ANTS_DIR=${ANTS_DIR}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show c3d/20150506 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep C3D_DIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE C3D_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("C3D_DIR=${C3D_DIR}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show naonlm/2.0 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep NAONLM_DIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE NAONLM_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("NAONLM_DIR=${NAONLM_DIR}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show miniconda ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep MINICONDA_DIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE MINICONDA_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  if("${MINICONDA_DIR}" STREQUAL "")
    message("Miniconda is not found. Set PYTHON_DIR manually.")
  else()
    message("Miniconda is found.")
    execute_process(COMMAND ${MINICONDA_DIR}/bin/conda env list OUTPUT_VARIABLE ev)
    execute_process(COMMAND echo ${ev} COMMAND grep ncanda-1.0.1 COMMAND rev COMMAND cut -d " " -f 1 COMMAND rev OUTPUT_VARIABLE PYTHON_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
    if("${PYTHON_DIR}" STREQUAL "")
      message("ncanda-1.0.1 Python environment is not found. Set PYTHON_DIR manually.")
    else()
      set(PYTHON_DIR "${PYTHON_DIR}/bin") 
      message("PYTHON_DIR=${PYTHON_DIR}")
    endif()
  endif()

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show workbench/1.2.3 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep CARET7_DIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE CARET7_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("CARET7_DIR=${CARET7_DIR}")

  execute_process(COMMAND ${MODULESHOME}/bin/modulecmd bash show msm/hocr_v1 ERROR_VARIABLE ev)
  execute_process(COMMAND echo ${ev} COMMAND grep MSM_DIR COMMAND cut -d " " -f 3 OUTPUT_VARIABLE MSM_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
  message("MSM_DIR=${MSM_DIR}")
endif()

if("${CMTKDIR}" STREQUAL "")
  set(CMTKDIR "NOTFOUND")
endif()
if("${FSLDIR}" STREQUAL "")
  set(FSLDIR "NOTFOUND")
endif()
if("${CAMINO_DIR}" STREQUAL "")
  set(CAMINO_DIR "NOTFOUND")
endif()
if("${ROBEX_DIR}" STREQUAL "")
  set(ROBEX_DIR "NOTFOUND")
endif()
if("${LWDP_DIR}" STREQUAL "")
  set(LWDP_DIR "NOTFOUND")
endif()
if("${AFNI_DIR}" STREQUAL "")
  set(AFNI_DIR "NOTFOUND")
endif()
if("${ITKSNAP}" STREQUAL "")
  set(ITKSNAP "NOTFOUND")
endif()
if("${FREESURFER_HOME}" STREQUAL "")
  set(FREESURFER_HOME "NOTFOUND")
endif()
if("${SLICER_CLI}" STREQUAL "")
  set(SLICER_CLI "NOTFOUND")
endif()
if("${ANTS_DIR}" STREQUAL "")
  set(ANTS_DIR "NOTFOUND")
endif()
if("${C3D_DIR}" STREQUAL "")
  set(C3D_DIR "NOTFOUND")
endif()
if("${NAONLM_DIR}" STREQUAL "")
  set(NAONLM_DIR "NOTFOUND")
endif()
if("${PYTHON_DIR}" STREQUAL "")
  set(PYTHON_DIR "NOTFOUND")
endif()
if("${CARET7_DIR}" STREQUAL "")
  set(CARET7_DIR "NOTFOUND")
endif()
if("${MSM_DIR}" STREQUAL "")
  set(MSM_DIR "NOTFOUND")
endif()

set(NCANDA_CMTKDIR ${CMTKDIR} CACHE PATH "${NCANDA_CMTKDIR_HELP}")
set(NCANDA_FSLDIR ${FSLDIR} CACHE PATH "${NCANDA_FSLDIR_HELP}")
set(NCANDA_CAMINO_DIR ${CAMINO_DIR} CACHE PATH "${NCANDA_CAMINO_DIR_HELP}")
set(NCANDA_ROBEX_DIR ${ROBEX_DIR} CACHE PATH "${NCANDA_ROBEX_DIR_HELP}")
set(NCANDA_LWDP_DIR ${LWDP_DIR} CACHE PATH "${NCANDA_LWDP_DIR_HELP}")
set(NCANDA_AFNI_DIR ${AFNI_DIR} CACHE PATH "${NCANDA_AFNI_DIR_HELP}")
set(NCANDA_ITKSNAP ${ITKSNAP} CACHE PATH "${NCANDA_ITKSNAP_HELP}")
set(NCANDA_FREESURFER_HOME ${FREESURFER_HOME} CACHE PATH "${NCANDA_FREESURFER_HOME_HELP}")
set(NCANDA_FREESURFER_QA_TOOLS ${FREESURFER_QA_TOOLS} CACHE PATH "${NCANDA_FREESURFER_QA_TOOLS_HELP}")
set(NCANDA_SLICER_CLI_DIR ${SLICER_CLI} CACHE PATH "${NCANDA_SLICER_CLI_DIR_HELP}")
set(NCANDA_ANTS_DIR ${ANTS_DIR} CACHE PATH "${NCANDA_ANTS_DIR_HELP}")
set(NCANDA_C3D_DIR ${C3D_DIR} CACHE PATH "${NCANDA_C3D_DIR_HELP}")
set(NCANDA_NAONLM_DIR ${NAONLM_DIR} CACHE PATH "${NCANDA_NAONLM_DIR_HELP}")
set(NCANDA_PYTHON_DIR ${PYTHON_DIR} CACHE PATH "${NCANDA_PYTHON_DIR_HELP}")
set(NCANDA_CARET7_DIR ${CARET7_DIR} CACHE PATH "${NCANDA_CARET7_DIR_HELP}")
set(NCANDA_MSM_DIR ${MSM_DIR} CACHE PATH "${NCANDA_MSM_DIR_HELP}")

set(SCRIPTS ncanda_setup.sh ncanda_all_pipelines ncanda_structural_pipeline ncanda_structural_cerebellum_pipeline ncanda_structural_reformat_to_template ncanda_freesurfer_pipeline ncanda_structural_all_pipelines ncanda_diffusion_pipeline ncanda_diffusion_freewater_pipeline ncanda_diffusion_post_pipeline ncanda_restingstate_pipeline ncanda_restingstate_longitudinal_pipeline  ncanda_epi_unwarp_siemens correct_dwi_distortion_and_motion correct_dwi_distortion_and_motion_2shell check_restingstate_output ncanda_freesurfer_longitudinal_pipeline ncanda_freesurfer_post_pipeline ncanda_restingstate_post_pipeline create_qc_image create_qc_longitudinal_images create_qc_images_all_visits ncanda_all_visits)

# Configure for the build tree
set(NCANDA_BINARY_DIR_CONFIG ${CMAKE_BINARY_DIR}/bin)
set(NCANDA_SOURCE_DIR_CONFIG ${CMAKE_SOURCE_DIR})
set(DATA_DIR_CONFIG ${CMAKE_CURRENT_SOURCE_DIR}/data)
foreach(s ${SCRIPTS})
  configure_file(${CMAKE_CURRENT_SOURCE_DIR}/templates/${s}.in ${CMAKE_BINARY_DIR}/bin/${s} @ONLY)
endforeach()

# Set the write permission for these files as svn automatically resets it to not being executable 
execute_process(COMMAND chmod 755 ${CMAKE_BINARY_DIR}/utils/rsfmri_specific_preprocessing.py)

