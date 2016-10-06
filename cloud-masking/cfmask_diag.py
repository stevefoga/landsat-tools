'''
cfmask_diag.py


Purpose: produce diagnostic layer for CFMask confidence band (from EROS 
         Science Processing Architecture (ESPA; https://espa.cr.usgs.gov)), 
         which indicates where tests either passed or failed in 
         algorithm workflow.


Inputs: Landsat 4-8 Top of Atmosphere (TOA) reflectance & brightness 
        temperature in .tar.gz archive. Supports both pre-collection and 
        Collection 1 Landsat data.


Outputs:  1) Diagnostic band.
          2) cfmask_conf band.


Diagnostic band (*_cfmask_diag.tif) interpretation:

  0000 0000 0001 = basic cloud test passed
  0000 0000 0010 = thermal threshold cloud test passed
  0000 0000 0100 = whiteness cloud test passed
  0000 0000 1000 = haze optimized test 1 is failed (still possibly cloud)
  0000 0001 0000 = haze optimized test 2 is failed (still possibly cloud)
  0000 0010 0000 = basic snow test passed (snow bit set)
  0000 0100 0000 = basic water test passed (water bit set)
  0000 1000 0000 = thermal thresh. confidence (test a) passed (high conf set)
  0001 0000 0000 = water cloud confidence (test b) passed (high conf set)
  0010 0000 0000 = land cloud confidence (test c) passed (high conf set)
  0000 0000 0002 = water cloud confidence (test d) passed (med conf set)
  0000 0000 0020 = land cloud confidence (test e) passed (med conf set)


cfmask_conf band (*_cfmask_conf_diag.tif) interpretation:

  0 = fill
  1 = low confidence
  2 = medium confidence
  3 = high confidence


Example usage:  python '/path/to/scripts/cfmask_diag.py' 
                '/path/to/data/LC80330422013173-SC20160914104656.tar.gz'


Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  14 September 2016
Modified: 06 October 2016
Version:  0.1x


Changelog:
  14-Sep-2016 - 0.1x - Original development.
  07-Oct-2016 - 1.0 - First correctly working version.


Caveats/Known issues:

  A) May not match 100% with CFMask product contained in Landast Collection 1 
      BQA.


Potential future work:

  1) Add cirrus test option.
  2) Add thermal disable option.
  3) Add cloud probability toggle option (hard-coded at 22.5)
  4) Add dilation for cloud; allow toggle of dilate buffer (hard-coded at 3)
  5) Add cloud shadow; allow toggle of  dilate buffer (hard-coded at 3)


Source:
  
  https://github.com/USGS-EROS/espa-cloud-masking/blob/master/cfmask/src/
    a) potential_cloud_shadow_snow_mask.c
    b) cfmask.c
    c) misc.c

'''
##############################################################################
import sys

def diag(input_gz):

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
  
  ## assign bands to colors, return dict
  def band_by_sensor(L8,bands):
    band_col = {}
    
    if L8 == True:
      band_col['blue']  = [i for i in bands if "band2" in i][0]
      band_col['green'] = [i for i in bands if "band3" in i][0]
      band_col['red']   = [i for i in bands if "band4" in i][0]
      band_col['nir']   = [i for i in bands if "band5" in i][0]
      band_col['swir1'] = [i for i in bands if "band6" in i][0]
      band_col['swir2'] = [i for i in bands if "band7" in i][0]
      band_col['therm'] = [i for i in bands if "band10" in i][0]
      
    else:
      band_col['blue']  = [i for i in bands if "band1" in i][0]
      band_col['green'] = [i for i in bands if "band2" in i][0]
      band_col['red']   = [i for i in bands if "band3" in i][0]
      band_col['nir']   = [i for i in bands if "band4" in i][0]
      band_col['swir1'] = [i for i in bands if "band5" in i][0]
      band_col['swir2'] = [i for i in bands if "band7" in i][0]
      band_col['therm'] = [i for i in bands if "band6" in i][0]
      
    return(band_col)

  
  ## read bands as array
  def read_bands(band_in):
    rast = gdal.Open(band_in,gdal.GA_ReadOnly)
    
    rast_arr = np.array(rast.GetRasterBand(1).ReadAsArray())
    
    return(rast_arr)
    
    
  ## calculate spectral index
  def calc_si(a,b):
    ## do calculation
    s_i = (a - b) / (a + b)
    
    ## if (a+b) == 0, set pixel(s) to 0.01
    s_i[np.where((a + b) == 0)] = 0.01
    
    return(s_i)
    
  
  ## clean up files
  def del_file(a):
    try:
      os.remove(a)
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
  dir_in = os.path.dirname(input_gz)
  
  bands = glob.glob(dir_in + os.sep + "*band*.tif")
  
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
  geo_out = gdal.Open(bands[0],gdal.GA_ReadOnly)
  
  ## read input files
  print("Reading input files as arrays...")
  blue = read_bands(band_col['blue'])
  
  ## make fill mask from blue band
  fz = np.zeros(np.shape(blue))
  fill = np.ma.masked_where(blue==-9999, fz)
  fz = None
  
  ## read in bands
  blue  = read_bands(band_col['blue']) 
  green = read_bands(band_col['green'])
  red   = read_bands(band_col['red'])
  nir   = read_bands(band_col['nir'])
  swir1 = read_bands(band_col['swir1'])
  swir2 = read_bands(band_col['swir2'])

  ## read thermal band (note it is scaled as [Celsius * 100])
  therm = ((read_bands(band_col['therm']) * 0.1) - 273.15) * 100

  ## calculate indices
  print("Calculating spectral indices...")
  ndvi = calc_si(nir,red)
  ndsi = calc_si(green,swir1)
  
    
  ############################################################################
  ## set hard-coded variables
  cloud_prob_threshold = 22.5
  t_buffer = 400.0
  

  ############################################################################
  ## do tests
  print("Basic test (diag bit 0)...")
  
  ## make initial array of zeros, equal to other arrays
  r0 = np.zeros(np.shape(blue), dtype="uint32")
  
  ## 1 == pixel potentially a cloud based upon said tests
  r0[np.where((ndsi < 0.8) & (ndvi < 0.8) & (swir2 > 300) 
               & (fill.mask == False))] = 1
  
  
  ############################################################################
  print("Thermal test (diag bit 1)...")
  r1 = np.zeros(np.shape(blue), dtype="uint32")
  
  ## 10 == pixel potentially a cluod based upon r0 and thermal test
  r1[np.where((r0 == 1) & (therm < 2700) & (fill.mask == False))] = 10
  
  
  ############################################################################
  print("Whiteness test (diag bit 2)...")
  r2 = np.zeros(np.shape(blue), dtype="uint32")
  sat = np.zeros(np.shape(blue), dtype="uint32")
  cld = np.zeros(np.shape(blue), dtype="uint32")
  
  ## mask out potentially non-cloud pixels found during previous tests
  b_c = np.ma.masked_where(r1 != 10, blue)
  g_c = np.ma.masked_where(r1 != 10, green)
  r_c = np.ma.masked_where(r1 != 10, red)
  
  ## get visible mean
  visi_mean = (b_c + g_c + r_c) / 3.0
  
  ## do whiteness calculation
  whiteness = (np.abs(b_c - visi_mean) + np.abs(g_c - visi_mean) 
              + np.abs(r_c - visi_mean)) / visi_mean
  
  ## mark whiteness as 100 if visi_mean == 0.0
  whiteness[np.where((visi_mean == 0.0) & (fill.mask == False))] = 100.0
  
  ## set saturation flag
  print("Setting saturation flag...")
  sat[np.where((b_c == 20000) | (g_c == 20000) | (r_c == 20000))] = 1
  print("# of saturated pixels: {0}".format(np.sum(sat == 1)))

  whiteness[np.where((sat == 1) & (fill.mask == False))] = 0.0
  
  ## 100 == pixel is cloud (r1 == 10) and if whiteness < 0.7
  r2[np.where((r1 == 10) & (whiteness < 0.7) & (fill.mask == False))] = 100
  
  ## set cloud bit (to be read/modified in later tests)
  cld[np.where((r1 == 10) & (fill.mask == False))] = 1
  
  print("# of cloud pixels marked as cloud before whiteness test: {0}".
          format(np.sum(cld == 1)))

  ## set all other potential cloud pixels failing whiteness test back to 0
  cld[np.where((r1 == 10) & (whiteness >= 0.7) & (fill.mask == False))] = 0

  ## clean up variables that aren't used later
  whiteness = None
  visi_mean = None
  g_c = None
  
  print("# of pixels failing the whiteness test: {0}".format(
       np.sum((r1 == 10) & (whiteness >= 0.7) & (fill.mask == False))))

  print("# of pixels still marked as cloud: {0}".format(np.sum(cld == 1)))
  
  ############################################################################
  print("Haze optimized tests (diag bits 3&4)...")
  r3 = np.zeros(np.shape(blue), dtype="uint32")
  r4 = np.zeros(np.shape(blue), dtype="uint32")
  
  s1_c = np.ma.masked_where(r1 != 10, swir1)
  n_c  = np.ma.masked_where(r1 != 10, nir)
  
  h1 = b_c - 0.5 * r_c  - 800.0
  
  ## 1,000 == hot1 failed, pixel is still cloud
  r3[np.where((h1 > 0.0) & (sat == 0) & (fill.mask == False))] = 1000
  
  ## remove cloud bit if hot1 failed
  cld[np.where((h1 <= 0.0) & (sat == 0) & (fill.mask == False))] = 0
  

  h2 = np.asfarray(n_c) / s1_c
  ## 10,000 == hot2 test failed, pixel still a cloud
  r4[np.where((fill.mask == False) & (h2 > 0.75))] = 10000
  
  ## remove cloud bit if hot2 passed
  cld[np.where((s1_c != 0.0) & (h2 <= 0.75) & (fill.mask == False))] = 0
  
  ## clean up vars
  h1 = None
  h2 = None
  b_c = None
  r_c = None
  n_c = None
  s1_c = None
  

  ############################################################################
  print("Basic snow test (diag bit 5)...")
  r5 = np.zeros(np.shape(blue), dtype="uint32")
  snow = np.zeros(np.shape(blue), dtype="uint32")
  
  snow[np.where((ndsi > 0.15) & (nir > 1100) & (green > 1000) & 
                (fill.mask == False))] = 1
  
  # 100,000 = pixel is snow
  r5[np.where((snow == 1) & (therm < 1000) & (fill.mask == False))] = 100000
  
  ## clean up vars
  snow = None
  
  
  ############################################################################
  print("Basic water test (diag bit 6)...")
  r6 = np.zeros(np.shape(blue), dtype="uint32")
  
  ## 1,000,000 = pixel is water
  r6[np.where( ((ndvi < 0.01) & (nir < 1100) & (fill.mask == False)) | 
                ((ndvi < 0.1) & (ndvi > 0.0) & (nir < 500) 
                & (fill.mask == False)) )] = 1000000
  
  print("No. of water pixels: {0}".format(np.sum(r6 == 1000000)))
  

  ############################################################################
  print("Setting clear water and clear land bits...")
  c_land = np.zeros(np.shape(blue), dtype="uint32")
  c_water = np.zeros(np.shape(blue), dtype="uint32")
  
  c_water[np.where((r6 != 0) & (cld == 0) & (fill.mask == False))] = 1
  c_land[np.where((r6 == 0) & (cld == 0) & (fill.mask == False))] = 1
  
  print("Counting clear bits, clear water bits, and clear lands bits...")
  
  ## determine number of clear pixels
  c_clear = np.sum((cld == 0) & (fill.mask == False))
   
  ## determine number of valid pixels
  c_count = np.sum(fill.mask == False)

  #c_clear = len(c_valid[c_valid == 1])
  c_land_count = np.sum((c_land == 1) & (fill.mask == False))
  c_water_count = np.sum((c_water == 1) & (fill.mask == False))
  
  #c_valid = None
 
  print("Total # of pixels: {0}".format(c_count))
  print("# clear pixels: {0}".format(c_clear))
  print("# water pixels: {0}".format(c_water_count))
  print("# land pixels: {0}".format(c_land_count))

  print("Calculating clear and water statistics...")
  ## clear percentage
  clear_ptm = float(c_clear) / float(c_count)
  
  if clear_ptm <= 0.1:
    print('\nWarning: scene is > 90% cloudy. Typical CFMask operation\n' 
          '(with dilation) writes the rest of the scenes non-cloud pixels\n'
          'as cloud shadow, its cloudy pixels as high-confidence cloud, and\n'
          'remaining thermal tests are disabled.\n')
  
  print("% of clear pixels: {0}".format(round(clear_ptm * 100.0,4)))
  
  ## clear water percentage
  water_ptm = float(c_water_count) / float(c_count)
  print("% of clear water pixels: {0}".format(round(water_ptm * 100.0,4)))
  
  ## clear land percentage
  land_ptm = float(c_land_count) / float(c_count)
  print("% of clear land pixels: {0}".format(round(land_ptm * 100.0,4)))
    

  ############################################################################
  ## land thermal test
  print("Calculating temperature statistics...")
  ## make sure enough land for test (>=10%), otherwise use all clear pixels
  if land_ptm >= 0.1:
    land_bt = therm[np.where((c_land == 1) & (sat != 1) 
                             & (fill.mask == False))]
    
    land_bit = c_land == 1
  
  else:
    print("Less than 10% cloud-free land. Using all clear pixels instead.")
    land_bt = therm[np.where((cld == 0) & (sat != 1) & (fill.mask == False))]

    land_bit = cld == 0

  if len(land_bt) == 0:
    print("No cloud-free land pixels. Setting land_bt to 0.")
    land_bt = 0
    

  ## water thermal test
  ## make sure enough water for test (>=10%), otherwise use all clear pixels
  if water_ptm >= 0.1:
    water_bt = therm[np.where((c_water == 1) & (sat != 1)
                              & (fill.mask == False) )]

    water_bit = c_water == 1
  
  else:
    print("Less than 10% cloud-free water. Using all clear pixels instead.")
    water_bt = therm[np.where((cld == 0) & (sat != 1) & (fill.mask == False))]
  
    water_bit = cld == 0

  if len(water_bt) == 0:
    print("No cloud-free water pixels. Setting water_bt to 0.")
    water_bt = 0
 

  ############################################################################
  ## calculate temperature percentiles
  print("Calculating temperature percentiles...")
  t_templ = np.percentile(land_bt, 17.5) - t_buffer
  print("t_templ: {0}".format(str(t_templ)))
  
  t_temph = np.percentile(land_bt, 82.5) + t_buffer
  print("t_temph: {0}".format(str(t_temph)))
  
  t_wtemp = np.percentile(water_bt, 82.5)
  print("t_wtemp: {0}".format(str(t_wtemp)))
  

  ############################################################################
  ## calculate cloud probability over water
  print("Calculating cloud probability over water...")
  
  brightness_prob = swir1 / 1100.0
  
  ## clip brightness prob between 0.0 and 1.0
  brightness_prob[brightness_prob < 0.0] = 0.0
  brightness_prob[brightness_prob > 1.0] = 1.0

  wtemp_prob = (t_wtemp - therm) / 400.0
  wtemp_prob[np.where((wtemp_prob < 0.0) & (fill.mask == False))] = 0.0
  
  brightness_prob = brightness_prob * wtemp_prob
  
  #w_p = brightness_prob * 100.0 
  wfinal_prob = brightness_prob * 100.0

  ## mask out non-water pixels
  #wfinal_prob = np.ma.masked_where(r6 != 0, w_p)
  
  ## clean up
  w_p = None
  brightness_prob = None
  wtemp_prob = None
  

  ############################################################################
  ## calculate cloud probability over land
  print("Calculating cloud probability over land...")
  ndvi_land = np.ma.masked_where(r6 == 0, ndvi)
  ndsi_land = np.ma.masked_where(r6 == 0, ndsi)

  ## ndvi and ndsi should not be negative
  ndvi_land[ndvi_land < 0.0] = 0.0
  ndsi_land[ndsi_land < 0.0] = 0.0

  visi_mean2 = (blue + green + red) / 3.0

  whiteness2 = (np.abs(blue - visi_mean2) + np.abs(green - visi_mean2) 
              + np.abs(red - visi_mean2)) / visi_mean2

  whiteness2[((visi_mean2 == 0.0) & (fill.mask == False))] = 0.0
  
  ## mask out saturation
  whiteness2[((sat == 1) & (fill.mask == False))] = 0.0

  whit_land = np.ma.masked_where(r6 == 0, whiteness2)
  
  ## find maximum pixel value in each stack of pixels
  vari_prob = 1.0 - np.max(np.dstack((abs(ndvi_land), abs(ndsi_land), 
                                      whit_land)),axis=2)

  #print("vari_prob: {0}".format(vari_prob))

  temp_prob = (t_temph - therm) / (t_temph - t_templ)
  temp_prob[np.where(temp_prob < 0.0)] = 0.0
  
  vari_prob = vari_prob * temp_prob
  
  #f_p = vari_prob * 100.0
  final_prob = vari_prob * 100.0

  ## mask out non-land pixels
  #final_prob = np.ma.masked_where(r6 == 0, f_p)

  ## clean up
  f_p = None
  temp_prob = None
  ndvi_land = None
  ndsi_land = None
  whit_land = None
  ndvi = None
  ndsi = None
  visi_mean2 = None
  whiteness2 = None

  
  ############################################################################
  ## calculate dynamic land cloud threshold
  print("Calculating dynamic land cloud threshold...")
  
  clr_mask = np.percentile(final_prob[((land_bit == True) & 
                                       (fill.mask == False))], 82.5)
  
  clr_mask = clr_mask + cloud_prob_threshold

  print("clr_mask: {0}".format(clr_mask))

  ## calculate dynamic water cloud threshold
  print("Calculating dynamic water cloud threshold...")
  
  wclr_mask = np.percentile(wfinal_prob[((water_bit == True) &
                                         (fill.mask == False))], 82.5)
  
  wclr_mask = wclr_mask + cloud_prob_threshold

  print("wclr_mask: {0}".format(wclr_mask)) 


  ############################################################################
  ## assign confidence levels
  print("Assigning confidence levels...")
  c_conf = np.zeros(np.shape(blue), dtype="uint32")
  
  ## a
  print("Confidence test a (diag bit 7)...")
  r7 = np.zeros(np.shape(blue), dtype="uint32")

  ## Note: all pixels passing test a will not be tested in subsequent tests
  c_conf[np.where((therm < (t_templ + t_buffer - 3500.0)) & 
                  (fill.mask == False))] = 3
  
  ## 10,000,000 == test a passed (high conf.)
  r7[np.where((therm < (t_templ + t_buffer - 3500.0)) & 
              (fill.mask == False))] = 10000000
  
  
  ## b
  print("Confidence test b (diag bit 8)...")
  r8 = np.zeros(np.shape(blue), dtype="uint32")
  c_conf[np.where((r6 != 0) & (wfinal_prob > wclr_mask) 
                 & (cld == 1) & (fill.mask == False) & (r7 == 0))] = 3
    
  ## 100,000,000 == test b passed (high conf over water)
  r8[np.where((r6 != 0) & (wfinal_prob > wclr_mask) 
             & (cld == 1) & (fill.mask == False) & (r7 == 0))] = 100000000
    
    
  ## c
  print("Confidence test c (diag bit 9)...")
  r9 = np.zeros(np.shape(blue), dtype="uint32")
  c_conf[np.where((r6 == 0) & (final_prob > clr_mask) 
                 & (cld == 1) & (fill.mask == False) & (r7 == 0))] = 3 
    
  ## 1,000,000,000 == test c passed (high conf over land)
  r9[np.where((r6 == 0) & (final_prob > clr_mask) 
             & (cld == 1) & (fill.mask == False) & (r7 == 0))] = 1000000000
    
    
  ## d
  print("Confidence test d (diag bit 10)...")
  r10 = np.zeros(np.shape(blue), dtype="uint32")
  c_conf[np.where((r6 != 0) & (wfinal_prob > wclr_mask - 10.0) 
                 & (cld == 1) & (fill.mask == False) & (r7 == 0)
                 & (r8 == 0))] = 2
    
  ## 2 == test d passed (medium conf over water)
  r10[np.where((r6 != 0) & (wfinal_prob > wclr_mask - 10.0) 
              & (cld == 1) & (fill.mask == False) & (r7 == 0)
              & (r8 == 0))] = 2
  

  ## e
  print("Confidence test e (diag bit 11)...")
  r11 = np.zeros(np.shape(blue), dtype="uint32")
  c_conf[np.where((r6 == 0) & (final_prob > clr_mask - 10.0) 
                 & (cld == 1) & (fill.mask == False) & (r7 == 0)
                 & (r9 == 0))] = 2
    
  ## 20 == test e passed (high conf over land)
  r11[np.where((r6 == 0) & (final_prob > clr_mask - 10.0) 
              & (cld == 1) & (fill.mask == False) & (r7 == 0)
              & (r9 == 0))] = 20
  

  ## f
  ## low confidence == 0, set to 1
  c_conf[np.where((c_conf == 0) & (fill.mask == False))] = 1
  

  ############################################################################
  ## sum tests at end
  print("Summing test diagnostics...")
  r_out = r0+r1+r2+r3+r4+r5+r6+r7+r8+r9+r10+r11
  
  ## write band of summed tests
  print("Writing out data...")
  
  ## make output file name
  fpath, fname = os.path.split(bands[0])
  
  if lsat_coll:
    ## if collection data, grab specific characters
    l_id = fname[0:40]
    
  else:
    ## if pre-collection data, grab specific characters
    l_id = fname[0:21]
    
  fn_out = fpath + os.sep + l_id + "_cfmask_diag.tif"
  fn_out_c = fpath + os.sep + l_id + "_cfmask_conf_diag.tif"  
  #visi_out = fpath + os.sep + l_id + "_visi_mean.tif"
  #whit_out = fpath + os.sep + l_id + "_whiteness_test.tif"
  fp_out = fpath + os.sep + l_id + "_prob.tif"
  fwp_out = fpath + os.sep + l_id + "_wprob.tif"
  #cld_out = fpath + os.sep + l_id + "_cld.tif"
  #ndvi_out = fpath + os.sep + l_id + "_ndvi.tif"
  #ndvi_l = fpath + os.sep + l_id + "_ndvi_land.tif"

  ## destroy bands if they already exist
  del_file(fn_out)
  del_file(fn_out_c)
  del_file(fp_out)
  del_file(fwp_out)
  #del_file(cld_out)
  #del_file(whit_out)
  #del_file(ndvi_out)
  #del_file(ndvi_l)
  #del_file(red_out)

  ## get band dimensions & geotransform
  ncol = geo_out.RasterXSize
  nrow = geo_out.RasterYSize
  
  ## create empty raster
  diag_ds = gdal.GetDriverByName('GTiff').Create(fn_out, ncol, nrow, 1, 
                                                 gdal.GDT_UInt32)
  conf_ds = gdal.GetDriverByName('GTiff').Create(fn_out_c, ncol, nrow, 1, 
                                                 gdal.GDT_Byte)
  fp_ds = gdal.GetDriverByName('GTiff').Create(fp_out, ncol, nrow, 1,
                                                 gdal.GDT_Float32)
  fwp_ds = gdal.GetDriverByName('GTiff').Create(fwp_out, ncol, nrow, 1,
                                                 gdal.GDT_Float32)
  
  #cld_ds = gdal.GetDriverByName('GTiff').Create(cld_out, ncol, nrow, 1,
  #                                                  gdal.GDT_Byte)
  #whit_ds = gdal.GetDriverByName('GTiff').Create(whit_out, ncol, nrow, 1,
  #                                                  gdal.GDT_Float32)
  #gc_ds = gdal.GetDriverByName('GTiff').Create(g_out, ncol, nrow, 1,
  #                                                  gdal.GDT_Float32)
  #ndvi_ds = gdal.GetDriverByName('GTiff').Create(ndvi_out, ncol, nrow, 1,
  #                                                  gdal.GDT_Float32)
  #ndvi_l_ds = gdal.GetDriverByName('GTiff').Create(ndvi_l, ncol, nrow, 1,
  #                                                  gdal.GDT_Float32)

  ## set grid spatial reference
  diag_ds.SetGeoTransform(geo_out.GetGeoTransform())
  conf_ds.SetGeoTransform(geo_out.GetGeoTransform())
  fp_ds.SetGeoTransform(geo_out.GetGeoTransform())
  fwp_ds.SetGeoTransform(geo_out.GetGeoTransform())
  #cld_ds.SetGeoTransform(geo_out.GetGeoTransform())
  #whit_ds.SetGeoTransform(geo_out.GetGeoTransform())
  #gc_ds.SetGeoTransform(geo_out.GetGeoTransform())
  #ndvi_ds.SetGeoTransform(geo_out.GetGeoTransform())
  #ndvi_l_ds.SetGeoTransform(geo_out.GetGeoTransform())

  diag_ds.SetProjection(geo_out.GetProjection())
  conf_ds.SetProjection(geo_out.GetProjection())
  fp_ds.SetProjection(geo_out.GetProjection())
  fwp_ds.SetProjection(geo_out.GetProjection())
  #cld_ds.SetProjection(geo_out.GetProjection())
  #whit_ds.SetProjection(geo_out.GetProjection())
  #gc_ds.SetProjection(geo_out.GetProjection())
  #ndvi_ds.SetProjection(geo_out.GetProjection())
  #ndvi_l_ds.SetProjection(geo_out.GetProjection())


  ## get band
  print("Writing diagnostic raster to {0}".format(fn_out))
  diag_ds.GetRasterBand(1).WriteArray(r_out)
  
  print("Writing confidence raster to {0}".format(fn_out_c))
  conf_ds.GetRasterBand(1).WriteArray(c_conf)

  print("Writing visi_mean raster to {0}".format(fp_out))
  fp_ds.GetRasterBand(1).WriteArray(final_prob)

  print("Writing visi_mean raster to {0}".format(fwp_out))
  fwp_ds.GetRasterBand(1).WriteArray(wfinal_prob)

  #print("Writing visi_mean raster to {0}".format(cld_out))
  #cld_ds.GetRasterBand(1).WriteArray(cld)

  #print("Writing visi_mean raster to {0}".format(whit_out))
  #whit_ds.GetRasterBand(1).WriteArray(whiteness)

  #print("Writing visi_mean raster to {0}".format(g_out))
  #gc_ds.GetRasterBand(1).WriteArray(g_c)

  #ndvi_ds.GetRasterBand(1).WriteArray(ndvi)
  #ndvi_l_ds.GetRasterBand(1).WriteArray(ndvi_land)
  ## close rasters
  diag_ds = None
  conf_ds = None
  visi_ds = None
  whit_ds = None
  bc_ds = None
  gc_ds = None
  rc_ds = None
  fp_ds = None
  fwp_ds = None
  cld_ds = None
  #ndvi_ds = None
  #ndvi_l_ds = None

  ## clean up files
  print("Cleaning up input bands...\n\n")
  for i in bands:
    del_file(i)

  del_file(glob.glob(fpath + os.sep + "*.xml")[0])
  
  t1 = time.time()
  total = t1 - t0
  print("Done.")
  print("End time: {0}".format(time.asctime()))
  print("Total time: {0} minutes.".format(round(total / 60,3)))
  
##############################################################################
if __name__ == "__main__":
  
  if len(sys.argv) != 2:
    print('Incorrect arguments. Required: /path/to/input_archive.tar.gz')
    print('Example use: python /path/to/scripts/cfmask_diag.py /path/to/\n'
          'LC80330422013173-SC20160914104656.tar.gz')
    sys.exit(1)
    
  else:
    diag(sys.argv[1])
