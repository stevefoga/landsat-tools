'''
generate_toa_bt.py

Purpose: Generate TOA reflectance or Brightness Temperature from Level 1
          Landsat data. Works with pre-collection or Collection 1 data.
          
         NOTE: this was written to aid in experimental projects. The Earth 
         Resources Observation and Science (EROS) Science Processing 
         Architecture (ESPA; https://espa.cr.usgs.gov) provides an easier/bulk
         ordering service to create this TOA and BT data.

         
Inputs:


Outputs:


Example usage:


Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  19 October 2016
Modified: 20 October 2016


Changelog:

    XX October 2016 - Finished original version

    
Source:

  Equations: http://landsat.usgs.gov/Landsat8_Using_Product.php

'''
##############################################################################
import sys

def gen_toa_bt(input_gz):

  ## load libraries
  import os                                                                
  import tarfile                                                            
  import glob
  import time
  import numpy as np
  try:    
    from osgeo import gdal
  except ImportError:
    import gdal
  
  t0 = time.time()
  print("Start time: {0}".format(time.asctime()))
  
  
  ############################################################################
  ## define functions
  
  ## read MTL.txt metadata file, return dict
  def read_mtl(mtl_f):
    ## define fields neede from MTL
    mtl_fields = ['K1_CONSTANT_BAND',
                  'K2_CONSTANT_BAND',
                  'REFLECTANCE_MULT_BAND',
                  'REFLECTANCE_ADD_BAND',
                  'SUN_ELEVATION']
    
    ## open MTL file
    with open(mtl_f) as f:
                      
      ## read for specific contents, put into dict
      mtl = {}
      
      for text in f:
        
        #text = f.readline()
        out = [text for i in mtl_fields if i in text]
          
        ## if a field matches
        if out:
            
          ## split the key and value, use strip() to remove whitespace 
          key = out[0].split(" = ")[0].strip()
          value = out[0].split(" = ")[1].split(",\n")[0].strip()
            
          ## put key in mtl dict, assign value
          mtl[key] = float(value)
        
    return(mtl)
  
  
  ## get cosine of solar zenith angle (xmus == name from ESPA TOA code)
  def xmus(mtl):
    
    try:
      
      cos_sza = np.cos(np.deg2rad(90 - float(mtl['SUN_ELEVATION'])))

      print("SUN_ELEVATION: {0}".format(str(mtl['SUN_ELEVATION'])))
      print("cosine sza: {0}".format(str(cos_sza)))
      
      return(cos_sza)
    
    except KeyError:
      
      print("Could not find SUN_ELEVATION from MTL!")
      sys.exit(1)
    
    
  ## assign bands to colors, return dict
  def band_by_sensor(L8,bands):
    band_col = {}
    
    if L8 == True:
      band_col['ca']    = [i for i in bands if "_B1." in i][0]
      band_col['blue']  = [i for i in bands if "_B2." in i][0]
      band_col['green'] = [i for i in bands if "_B3." in i][0]
      band_col['red']   = [i for i in bands if "_B4." in i][0]
      band_col['nir']   = [i for i in bands if "_B5." in i][0]
      band_col['swir1'] = [i for i in bands if "_B6." in i][0]
      band_col['swir2'] = [i for i in bands if "_B7." in i][0]
      band_col['cir']   = [i for i in bands if "_B9." in i][0]
      band_col['therm'] = [i for i in bands if "_B10." in i][0]
      band_col['therm2']= [i for i in bands if "_B11." in i][0]
      
      
    else:
      band_col['blue']  = [i for i in bands if "_B1." in i][0]
      band_col['green'] = [i for i in bands if "_B2." in i][0]
      band_col['red']   = [i for i in bands if "_B3." in i][0]
      band_col['nir']   = [i for i in bands if "_B4." in i][0]
      band_col['swir1'] = [i for i in bands if "_B5." in i][0]
      band_col['swir2'] = [i for i in bands if "_B7." in i][0]
      band_col['therm'] = [i for i in bands if "_B6." in i][0]
      print("Thermal band: {0}".format(band_col['therm']))

    return(band_col)

    
  ## read bands as array
  def read_bands(band_in):
    rast = gdal.Open(band_in,gdal.GA_ReadOnly)
    
    rast_arr = np.array(rast.GetRasterBand(1).ReadAsArray())
    
    return(rast_arr)
  
  
  ## find the band number (for output file naming)
  def get_band_no(fn_in):
    
    ## get just the band name
    fn = os.path.basename(fn_in)
    
    ## find band number
    band = fn.split(".TIF")[0][-3:]
    if "_" in band:
      band = band.split("_")[1]
    
    band_no = band.split("B")[-1]
    
    return(band_no)
    
  
  ## function to get geo params
  def get_geo_params(fn_in):

    ## open file in gdal
    geo_params = gdal.Open(fn_in, gdal.GA_ReadOnly) 

    return(geo_params)

  
  ## function to get TOA (spectral) radiance
  def spec_rad(band, m_l, a_l):
    
    ## do calculation
    s_rad = (float(m_l) * np.asfarray(band)) + a_l

    return(s_rad)


  ## function to compute Brightness Temperature
  def do_bt(band_in, k1, k2, ml, al):
    
    ## read bands
    t_band = read_bands(band_in)
    
    ## mask out nodata
    mask_band = np.ma.masked_where(t_band == 0, t_band)
    
    ## calculate spectral radiance
    s_rad = spec_rad(t_band, ml, al)
    
    ## calculate bt
    btemp = float(k2) / np.log((float(k1)/np.asfarray(s_rad)) + 1)
    
    btemp = np.ma.masked_where(mask_band == True, btemp)

    return(btemp)
    
    
  ## function to get multiplicative and additive rescaling refl. from MTL
  def toa_params(fn_in, mtl):
    
    ## get mp and ap with band numbers
    mult_b = float(mtl["REFLECTANCE_MULT_BAND_" + get_band_no(fn_in)])
    add_b =  float(mtl["REFLECTANCE_ADD_BAND_" + get_band_no(fn_in)])

    print("REFLECTANCE_MULT_BAND_{0}: {1}".format(str(get_band_no(fn_in)),
                                                  str(mult_b)))

    print("REFLECTANCE_ADD_BAND_{0}: {1}".format(str(get_band_no(fn_in)),
                                                 str(add_b)))
    
    return(mult_b, add_b)
  
  
  ## function to get multiplicative and additive rescaling radiance from MTL
  def rad_params(fn_in, mtl):
    
    ## get ml and al with band numbers
    mult_r = float(mtl["RADIANCE_MULT_BAND_" + get_band_no(fn_in)])
    add_r = float(mtl["RADIANCE_ADD_BAND_" + get_band_no(fn_in)])

    print("RADIANCE_MULT_BAND_{0}: {1}".format(str(get_band_no(fn_in)),
                                               str(mult_r)))

    print("RADIANCE_ADD_BAND_{0}: {1}".format(str(get_band_no(fn_in)),
                                              str(add_r)))

    return(mult_r, add_r)
  

  ## function to get K1 and K2 constants from MTL
  def bt_params(fn_in, mtl):
  
    if "B10" in fn_in:
      k1 = float(mtl['K1_CONSTANT_BAND_10'])
      print("B10 K1: {0}".format(str(k1)))

      k2 = float(mtl['K2_CONSTANT_BAND_10'])
      print("B10 K2: {0}".format(str(k2)))

    elif "B11" in fn_in:
      k1 = float(mtl['K1_CONSTANT_BAND_11'])
      print("B11 K1: {0}".format(str(k1)))

      k2 = float(mtl['K2_CONSTANT_BAND_11'])
      print("B11 K2: {0}".format(str(k2)))

    elif "B6." in fn_in:
      k1 = float(mtl['K1_CONSTANT_BAND_6'])
      print("B6 K1: {0}".format(str(k1)))

      k2 = float(mtl['K2_CONSTANT_BAND_6'])
      print("B6 K2: {0}".format(str(k2)))

    else:
      print("Could not find thermal constants!")
      print("Operating on file {0}".format(str(i)))
      sys.exit(1)
        
    return(k1, k2)
  
 
  ## function to compute TOA reflectance
  def do_toa(band_in, m_p, a_p, cos_sza):
    
    ## read bands
    o_band = read_bands(band_in)
    
    ## mask out nodata
    mask_band = np.ma.masked_where(o_band == 0, o_band)
    #print(type(mask_band))
    ## calculate toa
    toar = (float(m_p) * np.asfarray(o_band)) + a_p
    #print(type(toar))
    ## do sun angle correction
    toar = np.asfarray(toar) / float(cos_sza)
    #print(type(toar))  
    
    ## mask out nodata
    toar = np.ma.masked_where(mask_band == True, toar)
    
    return(toar)
  
  
  ## fucntion to write raster out to new file
  def write_raster(base_name, data_out, lsat_coll):
    
    print("Writing raster to file...")
    
    ## call function to get band number
    bnd_no = get_band_no(base_name)

    ## call function to get geo parameters for this band
    geo_params = get_geo_params(base_name)
    
    ## make output file name
    fpath, fname = os.path.split(base_name)

    if lsat_coll:
      ## if collection data, grab specific characters
      l_id = fname[0:40] + "_toa_band" + bnd_no

    else:
      ## if pre-collection data, grab specific characters
      l_id = fname[0:21] + "_toa_band" + bnd_no
    
    ## create output filename
    fn_out = fpath + os.sep + l_id + ".tif"
    
    ## get band dimensions
    ncol = geo_params.RasterXSize
    nrow = geo_params.RasterYSize

    ## create empty raster
    ds = gdal.GetDriverByName('GTiff').Create(fn_out, ncol, nrow, 1, 
                                              gdal.GDT_Int16)
    
    ## set grid spatial reference
    ds.SetGeoTransform(geo_params.GetGeoTransform())
  
    ## set grid projection
    ds.SetProjection(geo_params.GetProjection())
    
    ## set nodata value
    ds.GetRasterBand(1).SetNoDataValue(-9999)
    
    ## write band
    ds.GetRasterBand(1).WriteArray(data_out)
    
    ## close band (writes file)
    ds = None
  
  
  ## make .tar.gz with toa file(s)
  def make_tarfile(output_filename, source_files):
    
    with tarfile.open(output_filename, "w:gz") as tar:
        
       for i in source_files:
           
          tar.add(i, arcname=os.path.basename(i))  
  
  
  ## clean up files
  def del_file(a):
    
    try:
      for i in a:
        os.remove(i)
    
    except OSError:
      pass
      
      
  ############################################################################
  ## file i/o
  
  ## untar files
  t_o = tarfile.open(input_gz,'r:gz')
  
  print("Extracting files...")
  
  try:
    t_o.extractall(path=os.path.dirname(input_gz))
  except:
    print("Problem extracting .tar.gz file {0}".format(input_gz))
    sys.exit(1)
  
  ## find all band files
  print("Finding bands...")
  dir_in = os.path.dirname(input_gz)
  
  bands_1 = glob.glob(dir_in + os.sep + "*_B[1-9]*") ## bands 1-9
  bands_2 = glob.glob(dir_in + os.sep + "_*B[0-1][0-1]*") ## bands 10-11
  bands = bands_1 + bands_2
  
  ## find MTL file
  mtl_f = glob.glob(dir_in + os.sep + "*MTL.txt")[0]
  
  ## get MTL components
  mtl = read_mtl(mtl_f)
  
  ## get cosine of solar zenith angle (for TOA calc)
  cos_sza = xmus(mtl)
  
  ## get base name of first band
  fn = os.path.basename(bands[0])
  
  ## if Collection 1 data, check first four digits for sensor
  if fn[2] == '0':
  
    lsat_coll = True
    
    if fn[2:4] == '08':
      band_col = band_by_sensor(True,bands)
    else:
      band_col = band_by_sensor(False,bands)
  
  else:
  
    lsat_coll = False
    
    if fn[2] == '8':
      band_col = band_by_sensor(True,bands)
    else:
      band_col = band_by_sensor(False,bands)
  
  ## read first file for geo params for output band
  #geo_out = gdal.Open(bands[0],gdal.GA_ReadOnly)
  
  ## seperate thermal vs. optical bands
  therm_col = {}
  opt_col = {}
  
  for key in band_col:
    if 'therm' in key:
      therm_col[key] = band_col[key]
    else:
      opt_col[key] = band_col[key]
  
  
  ############################################################################
  ## do toa for optical bands
  print("Calculating TOA...")
  it = 0
  for i in opt_col:
    
    ## get toa params
    mp, ap = toa_params(opt_col[i], mtl)
    
    ## get toa
    toa_out = do_toa(opt_col[i], mp, ap, cos_sza)
    #print(type(toa_out))  
    ## rescale band
    toa_out = np.round(toa_out * 10000, 0)
    toa_out = toa_out.astype('int16')
    
    ## set nodata value
    toa_out[toa_out.mask == True] = -9999
    
    ## write out to raster
    write_raster(opt_col[i], toa_out, lsat_coll)

    it = it + 1
    print("TOA calculation {0} of {1} complete.".format(str(it), 
                                                        str(len(opt_col))))

  
  ############################################################################
  ## do bt for thermal band(s)
  ## read K1 and K2 from MTL
  k1 = [i for i in mtl if "K1" in i]
  k2 = [i for i in mtl if "K2" in i]
  
  it = 0
  for i in therm_col:
  
    ## get radiance params
    ml, al = rad_params(therm_col[i], mtl)
    
    ## get bt params
    k1, k2 = bt_params(therm_col[i], mtl)
    
    ## get bt
    #print(i)
    bt_out = do_bt(therm_col[i], k1, k2, ml, al)
    
    ## rescale band
    bt_out = np.round(bt_out * 100, 0)
    bt_out = bt_out.astype('int16')
    
    ## set nodata value
    bt_out[bt_out.mask == True] = -9999
    
    ## write out to raster
    write_raster(therm_col[i], bt_out, lsat_coll)
    
    it = it + 1
    print("BT calculation {0} of {1} complete.".format(str(it), 
                                                        str(len(therm_col))))
  
  
  ############################################################################
  ## g-zip (.tar.gz) toa/bt files & clean up
  output_gz = input_gz.split(".tar.gz")[0] + "_toa.tar.gz"
  toa_out = glob.glob(dir_in + os.sep + "*.tif")
  
  if len(toa_out) > 0:
    
    ## put files into archive
    print("Adding data to .tar.gz archive...")
    make_tarfile(output_gz, toa_out)
    
    print("File location: {0}".format(str(output_gz)))
    
    ## clean up everything else (txt, tif, TIF, jpg, png)
    print("Cleaning up files...")
    
    del_file(toa_out)
    del_file(glob.glob(dir_in + os.sep + "*.txt"))
    del_file(glob.glob(dir_in + os.sep + "*.png"))
    del_file(glob.glob(dir_in + os.sep + "*.jpg"))
    del_file(glob.glob(dir_in + os.sep + "*.TIF"))
    
  else:
    print("No TOA or BT files found!")
    sys.exit(1)

  
  ############################################################################
  ## end timer and print results
  t1 = time.time()
  total = t1 - t0
 
  print("End time: {0}".format(time.asctime()))
  print("Total time: {0} minutes.".format(round(total / 60,3)))
  print("Done.")


##############################################################################
if __name__ == "__main__":
  
  if len(sys.argv) != 2:
    print('Incorrect number of arguments.\n'
          'Arguments: generate_toa_bt.py /path/to/archive.tar.gz')
  
  else:
    gen_toa_bt(sys.argv[1])
