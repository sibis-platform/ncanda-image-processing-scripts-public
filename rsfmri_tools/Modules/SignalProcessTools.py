
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
import scipy.signal as sig
import scipy
import logging

from MiscTools import MiscTools
from ImageTools import ImageTools

log = logging.getLogger('module_logger')
from MiscTools import log_method


class SignalProcessTools(object):
    def __init__(self):
        self.misctools = MiscTools()
        self.imagetools = ImageTools()
    
    def low_pass_filter(self,input_signal, cutoff_freq, sample_freq, order):
        '''Wn : array_like
        A scalar or length-2 sequence giving the critical frequencies.
        For digital filters, `Wn` is normalized from 0 to 1, where 1 is the
        Nyquist frequency, pi radians / sample.  (`Wn` is thus in
        half-cycles / sample.)
        '''
        
        nyquist = sample_freq / 2.0
        Wn = cutoff_freq / nyquist   
        
        bev,alc = sig.butter(order, Wn, 'low' )
        
        output = sig.filtfilt(bev, alc, input_signal)
        
        return output
    
    def hi_pass_filter(self, input_signal, cutoff_freq, sample_freq, order):
        nyquist = sample_freq / 2.0
        Wn = (cutoff_freq / nyquist)                                                   
        bev, alc = sig.butter(order, Wn, btype='highpass' )
         
        out_put = sig.filtfilt(bev, alc, input_signal)
        
        return out_put
    
    @log_method 
    def butter_bandpass(self, lowcut, highcut, sample_rate, data, order=5):
        nyq = 0.5 * sample_rate
        low = lowcut / nyq
        high = highcut / nyq
        bev, alc = sig.butter(order, [low, high], btype='band', analog=False)#IIR filter
        
        out = sig.filtfilt(bev, alc, data)

        return out
  
    def periodogram_1D(self, data, sample_rate):
        data_fft = np.fft.fft(data)
        
        # throw out the dup and norm
        half_pt = np.floor(len(data_fft)/2.0)
        
        fft_uniq = data_fft[0:half_pt] / (half_pt - 1 )
        
        mag = 2 * np.abs(fft_uniq)
    
        # freq axis
        freq  = sample_rate # (s)
        nyquist = freq / 2.0
        num_pts = len(mag)
        freq_res = nyquist / float(num_pts)
        freq_vec = np.arange(0,nyquist, freq_res)
        
        return freq_vec, mag
    
    @log_method
    def flat_smooth(self, data, L=10):
        out = np.zeros(data.shape)
        for i in range(0, data.shape[0]-L):
            win = data[i:i+L]
            smoothed = np.mean(win)
            out[i:i+L] = smoothed
           
        return out    
    
    @log_method       
    def smooth(self, x, window_len=11, window='hanning', mode='valid', log_this=False):
        """smooth the data using alc window with requested size."""
       
        if x.ndim != 1:
            log.exception( "smooth only accepts 1 dimension arrays.")
            raise ValueError, "smooth only accepts 1 dimension arrays."
   
        if x.size < window_len:
            log.exception("Input vector needs to be bigger than window size.")
            raise ValueError, "Input vector needs to be bigger than window size."
   
        if window_len<3:
            return x
   
        if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
            log.exception("Windpw must be:'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")
            raise ValueError, "Windpw must be:'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
   
        s = np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
        #print(len(s))
        if window == 'flat': #moving average
            w = np.ones(window_len,'d')
        else:
            w = eval('np.' + window + '(window_len)')
   
        y = np.convolve(w / w.sum(), s, mode=mode)
    
        return y       
                       
    @log_method 
    def remove_global_drift(self, rs_path, mask, outfile, seg_len, deg=8):
        #rs = self.imagetools.load_image(rs_path)
        
        roi, ind, shape, coord = self.imagetools.get_roi(rs_path, mask)
        roi = roi.astype(scipy.float32, copy=False)
        
        roi -= roi.mean(axis=1, keepdims=True)      
        
        smooth = np.zeros((roi.shape[0], roi.shape[1] + seg_len - 1))
        for i in range(roi.shape[0]):
            smooth[i,:] = self.smooth(roi[i,:], seg_len, 'hanning', mode='valid')
         
        extra = np.float(seg_len -1)
        
        if np.mod(smooth.shape[1], extra) != 0.0:
            n = np.floor(smooth.shape[1] / np.float(extra))
            diff =  np.floor(smooth.shape[1] / np.float(n))
            
            if diff <= extra:
                pad_amt = extra - diff + 1
                pad = np.zeros((smooth.shape[0], pad_amt))
                rem_ind = np.arange(0, smooth.shape[1], n) 
                smooth = np.delete(smooth, rem_ind, axis=1)
                smooth = np.concatenate((smooth, pad), axis=1) 
            
            elif diff > extra:
                pad_amt = diff - extra + 1
                pad = np.zeros((smooth.shape[0], pad_amt))
                
                rem_ind = np.arange(0, smooth.shape[1], n) 
                smooth = np.delete(smooth, rem_ind, axis=1)
                smooth = np.concatenate((smooth, pad), axis=1) 
        
        t = np.arange(smooth.shape[1])    
        t_arr = np.tile(t, (roi.shape[0],1)).T
          
        pos = scipy.polyfit(t, smooth.T, deg)
        fit = scipy.polyval(pos, t_arr)    
        roi -=  fit.T
    
        new_image = np.zeros(shape, dtype=scipy.float32)
        new_image[ind] = roi
        
        log.info("Saving drift corrected image.")
        self.imagetools.save_new_image(new_image, outfile, coord)   
        #self.imagetools.save_new_image_clone(new_image, rs.header, outfile, coord)

    def norm_centered_roi_to_zero_one(self, infile, mask, outfile=None):   
            '''If you want to return only the normed roi, then do not use an 
            outfile arg. If you do want alc normed image written, then include an 
            outfile path in the args'''
             
            roi, ind, data_shape, coordmap = self.imagetools.get_roi(infile, mask)
            
            # un-center, make all positive
            # numpy is row major order, so reshape takes rows
            # and lays them down as cols
            mins = roi.min(axis=1,keepdims=True)
            roi -= mins 
    
            maxs = roi.max(1, keepdims=True)
            roi /= maxs
            
            roi -= np.mean(roi, axis=1, keepdims=True)
            
            new_image = np.zeros(data_shape, dtype=float)
            new_image[ind,:] = roi
            
            if outfile is not None:
                self.imagetools.save_new_image(new_image, outfile, coordmap ) 
            
            else:
                return roi

