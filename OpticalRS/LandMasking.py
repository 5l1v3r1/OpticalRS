# -*- coding: utf-8 -*-
"""
Created on Mon Jul 14 16:28:57 2014
This code also shows up in the Multispectral Land Masker QGIS plugin:
https://github.com/jkibele/LandMasker.
@author: jkibele
"""
import numpy as np
from scipy.ndimage.measurements import label

def connectivity_filter(in_array,threshold=1000,structure=None):
    """
    Take a binary array (ones and zeros), find groups of ones smaller
    than the threshold and change them to zeros.
    """
    #define how raster cells touch
    if structure:
        connection_structure = structure
    else:
        connection_structure = np.array([[0,1,0],
                                         [1,1,1],
                                         [0,1,0]])
    #perform the label operation
    labelled_array, num_features = label(in_array,structure=connection_structure)
    
    #Get the bincount for all the labels
    b_count = np.bincount(labelled_array.flat)
    
    #Then use the bincount to set the output values
    out_array = np.where(b_count[labelled_array] <= threshold, 0, in_array)
    
    #Respect the mask
    if np.ma.is_masked( in_array ):
        out_array = np.ma.MaskedArray( out_array, mask=in_array.mask )
    
    return out_array.astype( in_array.dtype )
    
def two_way_connectivity_filter( in_array, threshold=1000, structure=None):
    """
    Filter ones, then filter zeros
    """
    filtered1 = connectivity_filter( in_array, threshold, structure )
    filtered2 = ~connectivity_filter( ~filtered1, threshold, structure )
    return filtered2
    

def simple_land_mask(in_arr,threshold=50):
    """
    Return an array of ones and zeros that can be used as a land mask. Ones
    will be water and zeros will be land. This method fails to mask out
    shadows.
    
    Args:
        in_arr (numpy.array): An array of shape (Rows,Columns). Should be a NIR
            band. For WorldView-2 imagery, I use band 8.
        
        threshold (int or float): The pixel value cut-off. Pixels with a value
            lower than this will be considered water and be marked as 1 in the
            output.
            
    Returns:
        output (numpy.array): An array of 1s and 0s. 1s over water, 0s over 
            land.
            
    Note: the output from this method should be used as input for the 
        connectivity_filter method defined above. This will remove the isolated
        pixels on land that are marked as water.
    """
    band = in_arr
    # make a copy so we can modify it for output and still have the 
    # original values to test against
    output = band.copy()
    # pixels at or bellow threshold to ones
    output[np.where(band <= threshold)] = 1
    # zero out pixels above threshold
    output[np.where(band > threshold)] = 0
    # if it was zero originally, we'd still like it to be zero
    output[np.where(band == 0)] = 0
    
    return output
    
def mask_land(imarr, nir_threshold=100, conn_threshold=1000, structure=None):
    """
    Return a masked array where land is masked and water is not. This is 
    accomplished by looking at the longest wavelength band (assumed to be the
    last band), masking everything above nir_threshold, and then masking 
    unmasked pixels connected to fewer than conn_threshold unmasked pixels.
    
    Args:
        imarr (numpy.array): An array of shape (Rows,Columns,Bands). The
            multipectral image you wish to mask.
        
        nir_threshold (int or float): The pixel value cut-off. Pixels with a 
            value lower than this will be considered water and be left
            unmasked. Pixels with a value above will be considered land and
            will be masked.
            
        conn_threshold (int): Groups of unmasked pixels connected to fewer than
            this number of other unmasked pixels will be masked.
            
    Returns:
        output (numpy.ma.MaskedArray): A copy of imarr that has been masked. 
            The mask is generated from only one band but will be stacked as 
            many times as necessary to mask all the bands.
    """
    nirband = imarr[:,:,-1]
    simpmask = simple_land_mask( nirband, threshold=nir_threshold )
    #define how raster cells touch
    if structure:
        connection_structure = structure
    else:
        connection_structure = None
    mask1d = connectivity_filter( simpmask, threshold=conn_threshold, structure=connection_structure )
    
    nbands = imarr.shape[-1]
    mask = np.repeat( np.expand_dims(mask1d,2), nbands, axis=2 )
    return np.ma.masked_where( mask<>1, imarr )
    