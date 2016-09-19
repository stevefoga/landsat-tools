'''
convert_bqa_to_cloud.py


Purpose: Convert Landsat Collection 1 BQA to cloud Y/N band.


Usage: python convert_bqa_to_cloud.py 
        "/path/to/data/LC08_L1TP_033042_20130622_20160831_01_T1_BQA.TIF"


Output: 8-bit GeoTIFF raster where 0 = cloud; 1 = not cloud. Output example: 
        /path/to/data/LC08_L1TP_033042_20130622_20160831_01_T1_BQA_cloud.tif


Reference: http://landsat.usgs.gov/collectionqualityband.php


Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  09 September 2016
Edited:   19 September 2016
''' 
import sys
def qa_to_cloud(r_in):

  import os
  from osgeo import gdal
  import numpy as np
  
  ## read bands
  print("Reading band...")
  r = gdal.Open(r_in,gdal.GA_ReadOnly)
  
  ## read GDAL object as numpy array
  rast = np.array(r.GetRasterBand(1).ReadAsArray())
  
  ## get unique values
  print("Getting bits and converting to binary...")
  rast_uni = np.unique(rast)
  print("Cloud bits: {0}".format(rast_uni))
  
  ## check if bits are cloud
  for i in rast_uni:
    bin_str = bin(i)[2:].zfill(16)
    
    if bin_str[-5] == '1':
      rast[np.where(rast == i)] = 0
      
  ## make cloud bits 0, all others 1
  rast[np.where(rast != 0)] = 1  

  ## write band out as binary raster
  print("Writing band to raster...")
  
  fn_out = r_in.split(os.sep)[-1]
  dir_out = r_in.split(fn_out)[0]
  fn_out = fn_out.split(".TIF")[0] + "_cloud.tif"
  
  ## get band dimensions & geotransform
  ncol = r.RasterXSize
  nrow = r.RasterYSize
  
  ## create empty raster
  target_ds = gdal.GetDriverByName('GTiff').Create(dir_out+fn_out, ncol, nrow,
                                                   1, gdal.GDT_Byte)
  
  ## set grid spatial reference
  target_ds.SetGeoTransform(r.GetGeoTransform())
  target_ds.SetProjection(r.GetProjection())

  ## get band
  print("Writing raster to {0}".format(dir_out+fn_out))
  target_ds.GetRasterBand(1).WriteArray(rast)
  
  ## close raster
  target_ds = None
  
  print("Done.")

##############################################################################
if __name__ == "__main__":
  
  if len(sys.argv) != 2:
    print('Not enough arguments. Required: /path/to/data/input_raster.tif')
    print('Example use: python /path/to/script/convert_bqa_to_cloud.py\n' 
	        '/path/to/data/input_raster.tif')
    sys.exit(1)
  
  else:
    qa_to_cloud(sys.argv[1])
