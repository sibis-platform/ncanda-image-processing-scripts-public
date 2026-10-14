
##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
##  $HeadURL$
##  $Revision$
##  $LastChangedDate$
##  $LastChangedBy$
##

import glob
import subprocess
import re
from os import path
import os
import logging
import numpy as np

log = logging.getLogger('module_logger')

import functools
import inspect
from itertools import izip as itertools_izip

def log_method(func):
    
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # allows me to put the wrapper in helper methods that are sometimes major steps themselves.
        if 'log_this' in kwargs and kwargs['log_this'] is not False: 
            args_name = inspect.getargspec(func)[0][1:] #drop the 'self' arg
            args_dict = dict(list(itertools_izip(args_name, args)) + list(kwargs.iteritems()))
            method_name = wrapper.__name__
            args_dict_string = '\nMETHOD: ' + method_name + '\n'
            
            for k,v in args_dict.iteritems():
                if type(v) is not np.ndarray:
                    args_dict_string += "%s: %s\n" %(k,v)
            
                elif type(v) is np.ndarray:
                    args_dict_string += "NUMPY ARRAY:%s \nSHAPE:%s\n" %(k, str(v.shape))
             
            args_dict_string += '\n'
            log.info(args_dict_string)
            
        return func(self, *args, **kwargs) 
    
    return wrapper

class MiscTools(object):
    def __init__(self):
        pass

    @log_method
    def glob_for_files(self, root_dir, pattern, num_limit=1, log_this=False):
        files = glob.glob(path.join(root_dir, pattern))
        if len(files) == 0:
            log.warning("No files Found")
            return None
            #raise Exception, "No files founds with pattern: %s" %pattern
        elif len(files) > num_limit:
            raise Exception, "The number of files found were greater than the limit set: %i" %num_limit
        elif len(files) == 1 and num_limit ==1:
            return files[0]
        
        log.debug("File found with pattern: %s  In root dir: %s" %(pattern, root_dir))
        return files    

    def flatten_double_nested(self, list_ob):
        out =  [ item for sublist in list_ob for item in sublist ]

        return out

    def call_shell_program(self, cmd, catch_errors=True, catch_warnings=True):
        log.debug('command line used: %s' %cmd)
        
        process = subprocess.Popen(cmd, shell=True,
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)

        out, err = process.communicate()
        errcode = process.returncode
        
        log.debug('Shell call output: %s' %out)
        
        warn_ob = re.compile('.*warn.*', flags=re.IGNORECASE | re.DOTALL)
        error_ob = re.compile('.*error.*', flags=re.I | re.DOTALL)
        stop_ob = re.compile('.*STOPPING PROGRAM.*', flags=re.I)
        
        if catch_errors is True and (errcode or error_ob.match(err)): 
            print err
            log.debug('Shell call error mess: %s' %err)
            raise Exception, "%s %s" %(err, errcode)
        
        elif catch_warnings is True and  ( warn_ob.match(err) or stop_ob.match(err) or error_ob.match(err) ):
            print err
            log.debug('Shell call warning mess: %s' %err)
            raise Exception, "%s %s" %(err, errcode)
        
        return out
    
    def write_shell_script(self, prog_name, template):
        f = open(prog_name, 'w')
        f.write(template)
        f.close()
        os.chmod(prog_name, 0755)

    @log_method
    def ungzip(self, File, force=False, log_this=False):
        split_list = path.splitext(File)
        if split_list[-1] != '.gz':
            return File
        
        if force is True:
            cmd = 'gunzip -f %s' %File
        else:
            cmd = 'gunzip %s' %File
        
        self.call_shell_program(cmd)
        return split_list[0]

    @log_method
    def gzip(self, File, log_this=False):
        cmd = 'gzip %s' %File
        self.call_shell_program(cmd)
        
        return File + '.gz'

    def which(self, name, flags=os.X_OK):
        """
        http://twistedmatrix.com/trac/browser/tags/releases/twisted-8.2.0/twisted/python/procutils.py
        
        Search PATH for executable files with the given name.
       
        On newer versions of MS-Windows, the PATHEXT environment variable will be
        set to the list of file extensions for files considered executable. This
        will normally include things like ".EXE". This fuction will also find files
        with the given name ending with any of these extensions.
    
        On MS-Windows the only flag that has any meaning is os.F_OK. Any other
        flags will be ignored.
       
        @type name: C{str}
        @param name: The name for which to search.
       
        @type flags: C{int}
        @param flags: Arguments to L{os.access}.
       
        @rtype: C{list}
        @param: A list of the full paths to files found, in the
        order in which they were found.
        """
        result = []
        exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
        path = os.environ.get('PATH', None)
        if path is None:
            return []
        for pos in os.environ.get('PATH', '').split(os.pathsep):
            pos = os.path.join(pos, name)
            if os.access(pos, flags):
                result.append(pos)
            for e in exts:
                pext = pos + e
                if os.access(pext, flags):
                    result.append(pext)
        
        if len(result) == 0:
            raise Exception, "Program not found: %s" %name
        elif len(result) > 0:
            result = result[0]
        
        return result        

    def build_file_list(self, search_path, regex, string=True):
        out = []
        re_obj = re.compile(regex)
        files= os.listdir(search_path)
        
        for f in files:
            if re_obj.search(f):
                out.append(os.path.join(search_path, f))
            
        if string:
            out = " ".join(out)
        
        return out

    def check_if_gzipped(self, infile, unzip_if_true=True):
        
        if path.splitext(infile)[1] == '.gz':
            if unzip_if_true is True:
                infile = self.ungzip(infile) 
                return True, infile
            else:
                return True
                
        else:
            return False, infile
    
    @log_method    
    def untar_to_dir(self, tarfile, out_dir):
        cmd = "tar xvf  %(tarfile)s   --directory %(out_dir)s"

        cmd = cmd %{'tarfile':tarfile,
                    'out_dir':out_dir
                    } 
        
        self.call_shell_program(cmd)

