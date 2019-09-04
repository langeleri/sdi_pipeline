#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 29 13:10:04 2018

@author: andrew
"""
import sdi_pipeline
import requests
from .initialize import loc
from . import obtain
import os
import sys
from . import ref_image
from . import align_astroalign
from . import combine_numpy
from astropy.io import fits
from scipy.ndimage.filters import gaussian_filter
import numpy as np
import glob
from . import sex
from . import psf
from . import subtract_ais
from . import align_chi2
from . import align_imreg
from . import align_skimage
from . import check_saturation
from os import path

def TEST():
    #get data from LCO public archive and put in target directory under 'TEST' folder
    print("-> Getting data from LCO...")
    response = requests.get('https://archive-api.lco.global/frames/?' +
                            'RLEVEL=91&' +
                            'PROPID='+'standard&'
                            'OBJECT='+'L113&' + 
                            'FILTER='+'B&'
                            'start='+'2018-9-14'+'&' +
                            'end='+'2018-9-15'+'&'
                            ).json()
    
    frames = response['results']
    
    #delete bad images
    del_fr = []
    
    for fr in frames:
        if fr['id'] != 9602135 and fr['id'] != 9602132:
            del_fr.append(fr)
    
    for delete in del_fr:
        del frames[frames.index(delete)]
    
    #download data
    temp_loc = loc + '/sdi/temp/'
    os.mkdir(temp_loc+'test_data')
    for frame in frames:
      with open(temp_loc + 'test_data/' + frame['filename'], 'wb') as f:
        f.write(requests.get(frame['url']).content)
        
    #funpack and move to 'TEST' folder
    obtain.process()
    obtain.movetar()
    old_data_location = obtain.rename()
    data_location = old_data_location.replace('L113', 'TEST')
    print("test")
    os.rename(old_data_location, data_location)
    
    #align and combine images
    test_loc = data_location[:-5]
    check_saturation.check_saturate(test_loc + '/data')
    ref_image.ref_image(test_loc + '/data')
    align_astroalign.align2(test_loc + '/data')
#    align_skimage.skimage(test_loc + '/data')
    combine_numpy.combine_median(test_loc + '/data')
#    align_skimage.skimage_template(test_loc + '/data')
    
    #add three fake stars to reference image
    print("\n-> Adding fake stars to test image...")
    hdu = fits.getdata(test_loc + '/data/09:14:00.260_A_.fits')
    
    h, w = img_shape = np.shape(hdu)
    pos_x = [1500,2000,1200]
    pos_y = [1600,1400,2200]
    array = np.array([ 0.65343465,  0.50675629,  0.84946314])
    fluxes = 2000000.0 + array * 300.0
    img = np.zeros(img_shape)
    for x, y, f in zip(pos_x, pos_y, fluxes):
        img[x, y] = f
    
    img = gaussian_filter(img, sigma=15.0, mode='constant')
    
    final = fits.PrimaryHDU(hdu+img)
    final.writeto(test_loc + '/data/09:14:00.260_A_.fits', overwrite=True)
    
    #subtract images using ISIS
    subtract_ais.isis_sub_test(test_loc)
    
    #get PSFs then perform SExtractor on residual images
    sex.sextractor_psf(test_loc)
    psf.psfex(test_loc)
    sex.sextractor(test_loc)
    
    #test the results of the test function against known values
#    with open(test_loc + '/sources/sources.txt', 'r') as source:
#        lines = source.readlines()
#        source.close()
#    
#    with open(sdi_pipeline.module_path + '/test_config/test_sources.txt', 'r') as test_source:
#        lines2 = test_source.readlines()
#        test_source.close()
        
    res_image_loc = sdi_pipeline.module_path + '/test_config/09:14:00.260_A_residual_.fits'
    
    test_image_data = fits.getdata(res_image_loc)
    
    residual = glob.glob(test_loc + '/residuals/*_A_residual_.fits')
    
    residual_data = fits.getdata(residual[0])
#
#    if lines == lines2:
#        print("\t-> Sources matched to control")
    if test_image_data.all() == residual_data.all():
        print("-> Residuals matched to control\n-> TEST SUCCESSFUL!")
#    if lines == lines2 and test_image_data.all() == residual_data.all():
#        print("\t-> Test successful!")
    if test_image_data.all() != residual_data.all():
        print("-> Test failure: Results do not match controls")
    
    #display final residual test image
    os.system('ds9 %s -scale zscale' % (residual[0]))

if __name__ == '__main__':
    #get data from LCO public archive and put in target directory under 'TEST' folder
    print("-> Getting data from LCO...")
    response = requests.get('https://archive-api.lco.global/frames/?' +
                            'RLEVEL=91&' +
                            'PROPID='+'standard&'
                            'OBJECT='+'L113&' + 
                            'FILTER='+'B&'
                            'start='+'2018-9-14'+'&' +
                            'end='+'2018-9-15'+'&'
                            ).json()
    
    frames = response['results']
    
    #delete bad images
    del_fr = []
    
    for fr in frames:
        if fr['id'] != 9602135 and fr['id'] != 9602132:
            del_fr.append(fr)
    
    for delete in del_fr:
        del frames[frames.index(delete)]
    
    #download data
    temp_loc = loc + '/sdi/temp/'
    os.mkdir(temp_loc+'test_data')
    for frame in frames:
      with open(temp_loc + 'test_data/' + frame['filename'], 'wb') as f:
        f.write(requests.get(frame['url']).content)
        
    #funpack and move to 'TEST' folder
    obtain.process()
    obtain.movetar()
    data_location = obtain.rename()
    #data_location = old_data_location.replace('L113', 'TEST')
    #################################################
    #### TAKING THIS OUT FOR NOW 

    #if os.path.exists(data_location)
    #os.mkdir(data_location)
    #try:
    #    os.makedir(data_location)
    '''except OSError:
        print("Creation of dir %s failed" % data_location)
    else:
        print("Success!! Dir %s created " % data_location)
    '''
    print(("OLD: " + data_location))
    '''
    print("NEW: " + data_location)
    print(type(old_data_location))
    os.rename(old_data_location, data_location)
    '''
    #align and combine images
    test_loc = data_location[:-5]
    check_saturation.check_saturate(test_loc + '/data')
    ref_image.ref_image(test_loc + '/data')
    align_astroalign.align2(test_loc + '/data')
#    align_skimage.skimage(test_loc + '/data')
    combine_numpy.combine_median(test_loc + '/data')
#    align_skimage.skimage_template(test_loc + '/data')
    
    #add three fake stars to reference image
    print("\n-> Adding fake stars to test image...")
    hdu = fits.getdata(test_loc + '/data/09:14:00.260_A_.fits')
    
    h, w = img_shape = np.shape(hdu)
    pos_x = [1500,2000,1200]
    pos_y = [1600,1400,2200]
    array = np.array([ 0.65343465,  0.50675629,  0.84946314])
    fluxes = 2000000.0 + array * 300.0
    img = np.zeros(img_shape)
    for x, y, f in zip(pos_x, pos_y, fluxes):
        img[x, y] = f
    
    img = gaussian_filter(img, sigma=15.0, mode='constant')
    
    final = fits.PrimaryHDU(hdu+img)
    final.writeto(test_loc + '/data/09:14:00.260_A_.fits', overwrite=True)
    
    #subtract images using ISIS
    subtract_ais.isis_sub_test(test_loc)
    
    #get PSFs then perform SExtractor on residual images
    sex.sextractor_psf(test_loc)
    psf.psfex(test_loc)
    sex.sextractor(test_loc)
    
    #test the results of the test function against known values
#    with open(test_loc + '/sources/sources.txt', 'r') as source:
#        lines = source.readlines()
#        source.close()
#    
#    with open(sdi_pipeline.module_path + '/test_config/test_sources.txt', 'r') as test_source:
#        lines2 = test_source.readlines()
#        test_source.close()
        
    res_image_loc = sdi_pipeline.module_path + '/test_config/09:14:00.260_A_residual_.fits'
    
    test_image_data = fits.getdata(res_image_loc)
    
    residual = glob.glob(test_loc + '/residuals/*_A_residual_.fits')
    
    residual_data = fits.getdata(residual[0])
#
#    if lines == lines2:
#        print("\t-> Sources matched to control")
    if test_image_data.all() == residual_data.all():
        print("-> Residuals matched to control\n-> TEST SUCCESSFUL!")
#    if lines == lines2 and test_image_data.all() == residual_data.all():
#        print("\t-> Test successful!")
    if test_image_data.all() != residual_data.all():
        print("-> Test failure: Results do not match controls")
    
    #display final residual test image
    os.system('ds9 %s -scale zscale' % (residual[0]))