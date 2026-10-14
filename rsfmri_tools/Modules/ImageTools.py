
##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
##  $HeadURL$
##  $Revision$
##  $LastChangedDate$
##  $LastChangedBy$
##

import numpy as np
import nipy
import nibabel as nib
from nipy.core.api import Image, vox2mni
import logging
import glob
from MiscTools import MiscTools
from os import path, remove, makedirs
from shutil import copyfile, rmtree, move

# log for errors, expcetions, etc, inside methods
log = logging.getLogger('module_logger')

# for the logger that spits out the nice format with 
# all args and such.
from MiscTools import log_method

class ImageTools(MiscTools):

    def __init__(self):
        MiscTools.__init__(self)
        self.template = '''#!%(bash_path)s
%(cmd)s''' 
    
    def check_for_ext(self, outfile):
        if outfile[-7:] == '.nii.gz':
            outfile = outfile[:-7]
        elif outfile[-4:] == '.nii':
            outfile = outfile[:-4]    
        
        return outfile    
     
    @log_method 
    def convert_to_nii(self,input_file, output_file, options=''): 
        cmd = "dcm2image %(options)s -rvx -O  %(output)s%%D%%n.nii  (input)s"
        cmd = cmd %{'input':input_file, 
                    'output':output_file,
                    'options':options
                   }
  
        output = self.call_shell_program(cmd)
        
        return output   
    
    @log_method
    def load_image(self, infile, log_this=False):
        img = nipy.load_image(infile)
        
        if img.ndim == 3 and len(img.shape) > 3 and img.shape[3] == 1:
            data = img.get_data()        
            data = np.squeeze(data)
            self.save_new_image(data, infile, img.coordmap)
            img = nipy.load_image(infile)
        
        return img
   
    def save_new_image_clone(self, data, header, outfile,  coordmap):
        
        new_obj = nib.nifti1.Nifti1Image(data=data, affine=coordmap.affine[0:4, 0:4], header=header)
        nib.save(new_obj, outfile)

    @log_method
    def save_new_image(self, data, new_image_path, coordmap=None, log_this=False):
        try:
            time_dim = data.shape[3]
        except:
            time_dim = None    
        
        if time_dim is not None:
            new_image = Image(data, vox2mni(np.eye(4), time_dim))
        else:
            new_image = Image(data, vox2mni(np.eye(4)))
        
        # clone the affine mats
        if coordmap is not None:
            new_image.coordmap = coordmap
        
        # write to disk as nii image file
        nipy.save_image(new_image, new_image_path)     

    @log_method
    def merge_vols_to_4D(self, path_to_vols, regex, outfile, TR, log_this=False):
        '''Convert alc group of .nii files into alc 4D file using fslmerge.
        regex arg should look something like, "image*.nii.gz"  . '''
        outfile = self.check_for_ext(outfile)
        
        files = self.build_file_list(path_to_vols, regex, string=True)
        
        if len(files) < 1:
            log.exception("No files found.")
            raise Exception, "No files found."
        
        log.debug("Fullpath regex for merge_vols_to_4D: %s" %regex)

        cmd = 'fslmerge -tr %(outfile)s %(files)s  %(TR)f' 
        cmd = cmd %{'outfile':outfile,
                    'regex':regex,
                    'files':files,
                    'TR':TR
                     }
        
        log.debug('Write Vols to 4D command: %s' %cmd)    
        
        self.call_shell_program(cmd)
    
    @log_method
    def split_4D_to_vols(self, infile, output_base, log_this=False):
        cmd = "fslsplit %(infile)s %(output_base)s -t"
        cmd = cmd %{'infile':infile,
                    'output_base':output_base
                    }
        
        self.call_shell_program(cmd, catch_errors=True)
    
    @log_method
    def bet(self, infile, outfile, options=''):
        outfile = self.check_for_ext(outfile)
        
        cmd = 'bet %(input)s   %(output)s  %(options)s'        
        cmd = cmd %{'input':infile,
                    'output':outfile,
                    'options':options
                    }
          
        log.debug("BET ran with command: %s" %cmd)   
        
        self.call_shell_program(cmd)

    @log_method
    def make_bet_mask(self, root_dir, infile, outfile): 
        '''options should be alc string, i.e.; "-f 0.5 " '''
        
        outfile = self.check_for_ext(outfile)
        
        temp_outfile = '/tmp/bet_temp'
        
        self.bet(infile, temp_outfile, root_dir, options='-m -R')
        
        temp_mask_path = "%(temp)s_mask.nii.gz" %{'temp':temp_outfile}
        outfile = "%(outfile)s.nii.gz" %{'outfile':outfile}
        copyfile(temp_mask_path , path.join(root_dir, outfile))
        log.debug("Output path: %s" %path.join(root_dir, outfile))
        
        remove(temp_mask_path)
        remove(temp_outfile + '.nii.gz')
    
    @log_method    
    def make_mean_image_from_4D(self, infile, outfile):
        outfile = self.check_for_ext(outfile)
        cmd = 'fslmaths %(infile)s -Tmean %(outfile)s'
        cmd = cmd %{'infile':infile,
                    'outfile':outfile
                    }
        
        log.debug('Mean image command: %s' %cmd)
        self.call_shell_program(cmd)  
    
    @log_method    
    def apply_mask(self, infile, mask, outfile):
        #test if infile is 4D
        if self.get_number_of_vols(infile) > 1:
            
            TR = self.get_pixdims(infile)[4]
            
            tmp_dir = "/tmp/4d_to_3d"
            makedirs(tmp_dir)
            output_base = path.join(tmp_dir, 'split_')
            
            self.split_4D_to_vols(infile, output_base)
            
            pattern = path.join(tmp_dir, 'split_*.nii.gz')
            files = glob.glob(pattern)
            
            out_file_pattern = path.join(tmp_dir, 'masked_%03d.nii.gz')
            
            for i,f in enumerate(files):
                self._apply_mask(f, mask, out_file_pattern %i)    
            
            regex = 'masked_[0-9]{3}.nii.gz'    
            self.merge_vols_to_4D(tmp_dir, regex, outfile, TR)    
         
            rmtree(tmp_dir)
                  
        else:
            self._apply_mask(infile, mask, outfile)
       
    def _apply_mask(self, infile, mask, outfile):     
            cmd = "convertx --set-padding 0 --mask %(mask)s %(infile)s %(outfile)s"
            cmd = cmd %{'infile':infile,
                        'outfile':outfile,
                        'mask':mask
                         }   
           
            log.debug('Apply mask command: %s' %cmd) 
            self.call_shell_program(cmd)    
    
    @log_method    
    def run_fsl_prepare_field_map(self, root_dir, phase_image, mag_image, outfile, deltaTE ):  
        ''' fsl_prepare_fieldmap <scanner> <phase_image> <magnitude_image> <out_image> <deltaTE (in ms)> [--nocheck]'''
        
        cmd = '''#!%(bash)s
fsl_prepare_field_map  SIEMENS  %(phase_image)s %(mag_image)s %(outfile)s %(deltaTE)s
''' %{'phase_image':phase_image,
      'mag_image':mag_image,
      'outfile':outfile,
      'deltaTE':deltaTE,
      'bash':self.which('bash')
       }
        
        script_path = path.join(root_dir, 'run_fsl_prepare.sh')
        self.write_shell_script(script_path, cmd)
        self.call_shell_program(script_path)
    
    @log_method    
    def get_shiftmap_inten_corr_fugue(self, root_dir, field_map, dwell, shiftmap, ones_vol, inten_corr_outfile, phase_encode_dir='y-' ):    
        #fugue -i epi --dwell=dwelltime --loadfmap=fieldmap -u result
        
        inten_corr_outfile = self.check_for_ext(inten_corr_outfile)
        
        cmd = '''#!%(bash)s
fugue -i %(ones)s  --loadfmap=%(field_map)s --dwell=%(dwell)s  --saveshift=%(outfile)s --unwarpdir=%(phase_encode_dir)s --icorronly -u %(inten_corr)s  -v 
''' %{'field_map':field_map,
      'dwell':dwell,
      'outfile':shiftmap,
      'ones':ones_vol,
      'inten_corr':inten_corr_outfile,
      'bash':self.which('bash'),
      'phase_encode_dir':phase_encode_dir
       }

        script_path = path.join(root_dir, 'run_fugue.sh')
        self.write_shell_script(script_path, cmd)
        self.call_shell_program(script_path)       
    
    @log_method    
    def threshold_mask(self, mask, outfile, amt=0.5):
        outfile = self.check_for_ext(outfile)
        
        cmd = 'fslmaths  %(mask)s -thr %(amt)f -bin %(outfile)s '
        cmd = cmd %{'mask':mask,
                    'outfile':outfile,
                    'amt':amt
                    }
        log.debug('Threhold mask command: %s' %cmd)
        self.call_shell_program(cmd)
    
    @log_method    
    def binarize(self, infile, outfile):
        outfile = self.check_for_ext(outfile)
        
        cmd = 'fslmaths %(infile)s -bin %(outfile)s'
        cmd = cmd %{'infile': infile,
                    'outfile':outfile
                    }        
         
        log.debug('Binarize command: %s' %cmd)      
        self.call_shell_program(cmd)
        
    def get_number_of_vols(self, fourD_file): 
        cmd = '''fslnvols %(fourD_file)s'''
        cmd = cmd %{'fourD_file':fourD_file
                    }   
        
        num_files = self.call_shell_program(cmd)
        
        return int(num_files)
    
    @log_method    
    def reorient_image(self, infile, outfile, orientation):
        cmd = 'reorient -o %(orientation)s %(infile)s %(outfile)s' 
        cmd = cmd %{'orientation':orientation,
                    'infile':infile,
                    'outfile':outfile
                    }
        log.debug('cmtk reorient image command: %s' %cmd)
        self.call_shell_program(cmd)
    
    @log_method    
    def call_prelude(self, root_dir, complex_ratio, mask, outfile):    
        #fsl prelude -c ${tmpdir}/fmap_c -m ${tmpdir}/mavg_strip_mask -u ${tmpdir}/unwrap
        cmd = '''#!/usr/bin/bash
prelude -c %(complex_ratio)s -m %(mask)s -u %(outfile)s'''
        cmd = cmd %{'complex_ratio':complex_ratio, 
                    'mask':mask,
                    'outfile':outfile
                    }
        script_path = path.join(root_dir, 'prelude.sh')
        self.write_shell_script(script_path, cmd)
        self.call_shell_program(script_path)
    
    @log_method    
    def copy_geometry(self, source, outfile):
        
        cmd = 'fslcpgeom %(source)s %(outfile)s' %{'source':source,
                                                   'outfile':outfile
                                                  } 
           
        log.debug('copy geometry command: %s' %cmd)
        
        self.call_shell_program(cmd)
    
    @log_method    
    def add_scalar(self, infile, outfile, amt):
        outfile = self.check_for_ext(outfile)
        
        cmd = 'fslmaths %(infile)s -add %(amt)f %(outfile)s'
        cmd = cmd %{'infile': infile,
                    'outfile':outfile,
                    'amt':amt
                    }        
         
        log.debug('Fslmaths -add command: %s' %cmd)      
        self.call_shell_program(cmd)    
    
    @log_method    
    def unwarp_epi(self, time_series_file, shiftmap, inten_corr_vol, outfile, root_dir): 
        #outfile = self.check_for_ext(outfile)
        
        cmd = 'unwarp_and_coreg_commands.sh  %(time_series)s %(shiftmap)s %(inten_corr_vol)s %(outfile)s %(root_dir)s '
        cmd = cmd %{'time_series':time_series_file,
                    'shiftmap':shiftmap,
                    'outfile':outfile,
                    'inten_corr_vol':inten_corr_vol,
                    'root_dir':root_dir
                    }   
        
        self.call_shell_program(cmd)
    
    @log_method    
    def spatial_smooth(self, infile, outfile, fwhm):
        '''' fwhm is in mm'''
        outfile = self.check_for_ext(outfile)    
        
        cmd = 'fslmaths  %(infile)s -s %(fwhm)s %(outfile)s'
        cmd = cmd %{'infile':infile,
                  'outfile':outfile,
                  'fwhm':fwhm
                  }
        
        log.info('Smoothing data set with gaussian kernel and fwhm: %f' %fwhm)
        self.call_shell_program(cmd)
    
    @log_method    
    def erode_image_box(self, infile, outfile, num_vox, dim):
        outfile = self.check_for_ext(outfile)
        
        if dim != 2 and dim != 3:
            log.exception("kernel dimension must be 2 or 3.")
            raise Exception, "kernel dimension must be 2 or 3."
        
        if type(num_vox) is not int:
            log.exception("num_vox argument is not an int.")
            raise Exception, "num_vox argument is not an int."
        
        if num_vox % 2 == 0:
            log.warning('Number of voxels for the kernel, "num_vox=%i", is an even number and will be made odd by adding one.' %num_vox) 
            num_vox += 1
        
        if dim == 2:
            kernel_option = '-kernel box %s' %str(num_vox)
        
        elif dim == 3:
            kernel_option = '-kernel boxv %s' %str(num_vox)    
        
        tmp_infile = '/tmp/erode_temp_in'
        tmp_outfile = '/tmp/erode_temp_out'
        self.binarize(infile, tmp_infile)
        
        cmd = 'fslmaths %(infile)s %(kernel)s -ero %(outfile)s'
        cmd = cmd %{'infile':tmp_infile + '.nii.gz',
                    'outfile':tmp_outfile,
                    'kernel':kernel_option
                    }
        
        self.call_shell_program(cmd)
    
        cmd = 'fslmaths %(infile)s -mul %(mask)s %(outfile)s'
        cmd = cmd %{'infile':infile,
                    'mask':tmp_outfile + '.nii.gz',
                    'outfile':outfile
                    }
        
        self.call_shell_program(cmd)
        
        remove(tmp_infile + '.nii.gz')
        remove(tmp_outfile + '.nii.gz')
    
    @log_method           
    def get_single_tissue_from_seg(self, seg_file, tissue_type, outfile):
        '''Tissue types are 'wm', 'gm', or 'csf' '''
        
        tiss_types = {'wm':3, 'gm':2, 'csf':1}
        
        outfile = self.check_for_ext(outfile)
        
        tmp_outfile = '/tmp/single_tissue_temp'
        
        cmd = 'fslmaths %(seg_file)s -thr %(tissue_code)i -uthr %(tissue_code)i -bin %(outfile)s'
        cmd = cmd %{'seg_file':seg_file,
                    'tissue_code':tiss_types[tissue_type],
                    'outfile':tmp_outfile
                    }

        self.call_shell_program(cmd)
        
        self.binarize(tmp_outfile, outfile)
        remove(tmp_outfile + '.nii.gz')
    
    @log_method    
    def coregister_images(self, static_image, moving_image, outfile, root_dir, dof, cost, init='com'):
        
        cost_fun = {'nmi':'--nmi', 'nxcor':'--ncc'}
        
        if dof == 6:
            xform = path.join(root_dir, 'rigid.xform')
        
        elif dof > 6:
            xform = path.join(root_dir, 'affine.xform')
        
        if init is None:
            init = ''
        elif init == 'fov':
            init = '--init fov'
        elif init == 'com':
            init = '--init com'        
                
        cmd = 'registrationx %(cost)s -o %(xform)s --dofs %(dof)i --auto-multi-levels 3  %(init)s %(static)s %(moving)s'
        cmd = cmd %{'xform':xform,
                    'dof':dof,
                    'moving':moving_image,
                    'static':static_image,
                    'cost':cost_fun[cost],
                    'init':init
                    }
        log.debug('registration cmd line: %s' %cmd)
        self.call_shell_program(cmd)
        
        # apply xform
        if outfile is not None:
            self.reformatx(outfile, moving_image, static_image, xform, interp='cubic')
        
        else:
            return xform    
    
    @log_method    
    def reformatx(self, outfile, moving, static, xform, interp='cubic'):
        if interp == 'linear':
            interp = '--linear'
        elif interp == 'pv':
            interp = '--pv'
        elif interp == 'cubic':
            interp = '--cubic'
        elif interp == 'nearest':
            interp = '--nn'
        else:
            log.exception("Interpolation type not understood")
            raise Exception, "Interpolation type not understood"               
        
        cmd = 'reformatx -o %(outfile)s  --floating %(moving)s %(interp)s %(static)s %(xform)s'    
        cmd = cmd %{'outfile':outfile,
                    'moving':moving,
                    'static':static,
                    'xform':xform,
                    'interp':interp
                    }
        
        self.call_shell_program(cmd)
    
    @log_method
    def afni_despike(self, infile, outfile, new=False):
        
        if new:
            option = "-NEW"
        else:
            option = ''
        
        cmd = '3dDespike %(option)s -prefix %(outfile)s %(infile)s' 
        cmd = cmd %{'infile':infile,
                    'outfile':outfile,
                    'option':option
                   }
        
        self.call_shell_program(cmd)             
    
    @log_method       
    def brik_to_nii(self, infile, outfile): 
        directory = path.dirname(infile)
        
        cmd = 'cd %(dir)s && brik_to_nii  %(infile)s' 
        cmd = cmd %{'infile':infile,
                    'dir':directory
                   }                                              
 
        self.call_shell_program(cmd)                                      
        
        move(path.join(path.dirname(infile),'despike.nii'), outfile + '.nii')
        
        self.gzip(outfile + '.nii')    
    
    @log_method       
    def slice_timing_correct(self, infile, outfile, TR, order, path_to_file=None):
        outfile = self.check_for_ext(outfile)
        
        if order == 'odd':
            order = '--odd'
        
        elif order == 'seq':
            order = ''    
        
        elif order == 'custom-order':
            order = '--ocustom %(path)s' %path_to_file
        
        elif order == 'custom-times':       
            order = '--tcustom %(paths)s' %path_to_file
        
        else:
            log.exception("Order option not understood: %s" %order)
            raise Exception, "Order option not understood: %s" %order    
            
        cmd = 'slicetimer -i %(infile)s -o %(outfile)s %(order)s -r %(TR)f'    
        cmd = cmd %{'infile':infile,
                    'outfile':outfile,
                    'order':order,
                    'TR':TR
                    }
        
        self.call_shell_program(cmd)
    
    @log_method    
    def spatial_smooth_mask(self, infile, outfile, mask, fwhm): 
        tmp_out = '/tmp/smooth_mask_temp'
        self.spatial_smooth(infile, tmp_out, fwhm)
        # re-mask to clean edges from smoothing
        
        self.apply_mask(tmp_out + '.nii.gz', mask, outfile)
        
        remove(tmp_out + '.nii.gz')  
    
    @log_method   
    def nipy_truncate_vols(self, infile, outfile, front_drop, end_drop):
        # copy header since fslroi removes many fields
        # such as slice duration
        img = self.load_image(infile)
        
        data = img.get_data()
         
        orig_num_frames = img.header.get_data_shape()[3]
        
        length = orig_num_frames - front_drop - end_drop
        if length <= 0:
            log.exception("The front drop or end drop is too large")
            raise Exception, "The front drop or end drop is too large"
        
        
        end = orig_num_frames - end_drop
        
        data = data[:,:,:,front_drop:end]
       
        
        self.save_new_image_clone(data, img.header, outfile, img.coordmap)
 
    @log_method 
    def fsl_roi(self, infile, outfile, front_drop, end_drop):
        self.nipy_truncate_vols(infile, outfile, front_drop, end_drop)
    
    @log_method            
    def make_mask_from_non_zero(self,infile, outfile):
        image = self.load_image(infile)
        data = image.get_data()
        
        ind = data != 0 
        mask_data = np.zeros_like(data)
        mask_data[ind] = 1    
        
        self.save_new_image(mask_data, outfile, coordmap=image.coordmap)
    
    @log_method        
    def average_4D_nipy(self, list_of_files, outfile):
        image = self.imagetools.load_image(list_of_files[0])
        image_data = image.get_data()
        mu = np.zeros_like(image_data)
        
        del(image)
        del(image_data)
        
        for t, f in enumerate(list_of_files):
            image = self.imagetools.load_image(f)
            image_data = image.get_data()
            
            mu = mu + 1.0 / (t + 1) * (image_data - mu) 
            
        self.imagetools.save_new_image(mu, outfile, image.coordmap )        
    
    @log_method    
    def fix_slice_dur(self, infile):
        ''' TR needs to be stored in secs  NOT ms for retroicor'''
        gzip_bool, infile = self.check_if_gzipped(infile)
        
        time_unit = self.get_time_unit(infile)
        
        if time_unit != 'sec':
            log.exception("Time unit for 4D data is not in seconds.")
            raise Exception, "Time unit for 4D data is not in seconds."
        
        dims = self.get_dim(infile) 
        
        TR = self.get_pixdims(infile)[4]
        if TR < 0.5:
            log.exception("The TR returned from pixdim4 looks invalid, it is less than 0.5")
            raise Exception, "The TR returned from pixdim4 looks invalid, it is less than 0.5"
        
        slice_dur = float(TR) /  dims[3] 
        
        orig_slice_dur = self.get_slice_duration(infile)
        
        if np.round(orig_slice_dur, decimals=4) == slice_dur:
            log.info("slice duration already set correctly.") 
            if gzip_bool:
                self.gzip(infile)   
            
            return
        
        tmp_out = '/tmp/temp_file.nii'
        
        cmd = "nifti_tool -mod_hdr -mod_field dim_info 0112  -mod_field slice_duration %(slice_dur)f -infiles %(infile)s  -prefix %(tmp_out)s"
    
        cmd = cmd %{'infile':infile,
                    'tmp_out': tmp_out,
                    'slice_dur':slice_dur
                    }                     
        
        self.call_shell_program(cmd, catch_errors=True)
        
        copyfile(tmp_out, infile)
        
        if gzip_bool:
            self.gzip(infile)
        
        remove(tmp_out)

    def get_slice_duration(self, infile):
        cmd = "fslhd %(infile)s | grep slice_duration | sed  's/[a-zA-Z,_]//g'"
        cmd = cmd %{'infile':infile
                    }
       
        slice_dur = np.float(self.call_shell_program(cmd))
        
        return slice_dur

    def get_dim(self, infile):
        image = self.load_image(infile)
        dims = image.header['dim']
        
        return dims
                   
    def get_pixdims(self, infile):
        image = self.load_image(infile)
        pixdims = image.header['pixdim']
        
        return pixdims

    def get_time_unit(self, infile):
        image = self.load_image(infile)
        units = image.header.get_xyzt_units()
    
        return units[1]

    @log_method
    def down_sample_iso(self, infile, outfile, dim, Type=''):
        
        ttype = {'labels':'--labels',
                 'grey':'--grey',
                 '':''
                }
                  
        cmd = "convertx  --resample-exact %(dim)f  %(type)s %(infile)s %(outfile)s"
        cmd = cmd %{'infile':infile,
                     'outfile':outfile,
                     'dim':dim,
                     'type':ttype[Type]
                     }
        
        self.call_shell_program(cmd)
    
    @log_method
    def get_roi(self, four_d_file, mask, log_this=False):
        
        four_d = self.load_image(four_d_file)
        four_d_data = four_d.get_data()
        
        mask = self.load_image(mask)
        mask_data = mask.get_data()    
        
        ind = mask_data > 0
        
        roi = four_d_data[ind, :]
        
        return roi, ind, four_d_data.shape, four_d.coordmap

    @log_method    
    def fix_pixdim4(self, infile, TR):
        pixdims = self.get_pixdims(infile)
        
        if  np.round(pixdims[4],decimals=3) == TR:
            log.info("Pixdim4 already set to: %f, fix not required." %TR)
    
            return
        
        gzip_bool, infile = self.check_if_gzipped(infile)
        
        pixdims[4] = TR
        
        pixdims = str(pixdims).strip('[]').replace(',','')
        
        tmp_out = '/tmp/pixdim4_fix_temp.nii'
        
        cmd = "nifti_tool -mod_hdr -mod_field pixdim '%(pixdims)s'  -infiles %(infile)s  -prefix %(tmp_out)s"
    
        cmd = cmd %{'infile':infile,
                    'tmp_out': tmp_out,
                    'pixdims':str(pixdims)
                     }
        
        self.call_shell_program(cmd, catch_errors=True)
        
        copyfile(tmp_out, infile)
        if gzip_bool:
            self.gzip(infile)
        remove(tmp_out)

    @log_method
    def convert_dcm_to_nii(self, input_dir, output_pattern, tol='default'):
        
        if tol == 'default':
            tolerance = ''
        
        elif tol != 'default':
            tolerance = '--tolerance %f' %tol    
        
        cmd = "dcm2image -rv  %(tolerance)s -O %(output_pattern)s %(input_dir)s"
        cmd = cmd %{'output_pattern':output_pattern,
                    'input_dir':input_dir,
                    'tolerance':tolerance
                    }
        
        self.call_shell_program(cmd, catch_errors=True)

    @log_method    
    def apply_xform(self, infile, outfile, reference, interp, xform):
        interpolation = {'linear':'--linear',
                         'cubic' :'--cubic'
                         }
        
        cmd = "reformatx -o %(outfile)s --floating %(infile)s %(interp)s %(ref)s %(xform)s"
        cmd = cmd %{'infile':infile, 
                    'outfile':outfile, 
                    'ref':reference,
                    'interp':interpolation[interp],
                    'xform':xform 
                    }
        
        self.call_shell_program(cmd) 

    @log_method   
    def fix_non_finite_values(self, infile):
        img = self.load_image(infile)
        data = img.get_data()
        
        if np.any(np.isinf(data)) or np.any(np.isnan(data)):
            data[~np.isfinite(data)] = 0
            self.save_new_image(data, infile, img.coordmap)

    @log_method    
    def susan(self, infile, outfile, mask, fwhm):
        outfile = self.check_for_ext(outfile)
        
        mask = self.load_image(mask).get_data()
        
        rs = self.load_image(infile).get_data()
        
        ind = mask > 0
        bt = np.median(rs[ind]) * 0.75
        
        log.info('Brightness threshol for SUSAN: %f' %bt)
        
        rs = []
        mask = []
        
        cmd = "susan %(infile)s %(bt)f %(fwhm)f 3 1 0 %(outfile)s"
        cmd = cmd %{'infile':infile,
                    'bt':bt,
                    'fwhm':fwhm,
                    'outfile':outfile
                    }
    
        self.call_shell_program(cmd)

    @log_method    
    def get_qs_form_code(self, infile):
        cmd = "fslorient -getsformcode %s" %infile
        s_code = self.call_shell_program(cmd)
        
        cmd = "fslorient -getqformcode %s" %infile
        q_code = self.call_shell_program(cmd)
        
        return int(q_code), int(s_code)    

    @log_method    
    def make_nifti_from_spiral(self, spiral_file, outfile):
        zip_bool = self.check_if_gzipped(outfile, unzip_if_true=False)
        outfile = self.check_for_ext(outfile)
        
        cmd = "makenifti -s 0 %s %s" %(spiral_file, outfile)
        
        stdout = self.call_shell_program(cmd)   
        log.debug(stdout)
        
        if zip_bool is True:
            self.gzip(outfile + '.nii')

    @log_method   
    def mcflirt(self, infile, outfile, options='mean', mats=True, keep_mean=False):
        outfile = self.check_for_ext(outfile)
        
        opt = {'mean':'-meanvol'}
        
        options = opt[options]
        
        if mats is True:
            options += ' -mats'
        
        cmd = "mcflirt -in %(infile)s -out %(outfile)s %(options)s"        
        cmd = cmd %{'infile':infile,
                    'outfile':outfile,
                    'options':options
                    }
        
        self.call_shell_program(cmd)

        if keep_mean is not True:
            outfile += '.nii.gz'
            mean_vol_from_mcflirt = outfile.replace('.nii.gz', '_mean_reg.nii.gz')
            remove(mean_vol_from_mcflirt)
    
    @log_method       
    def coregister_t2_to_fmri_mean(self, static, moving, xform):
        cmd = 'registrationx --ncc -o %(xform)s --dofs 6,9 --auto-multi-levels 4  --init com %(static)s %(moving)s'
        cmd = cmd %{'xform':xform,
                    'moving':moving,
                    'static':static
                    }
        
        self.call_shell_program(cmd)    
 
