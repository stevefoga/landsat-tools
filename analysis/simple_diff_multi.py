"""
function simple_diff_multi.py


Purpose: Diff two image files, and output diff image + statistics.


Example use: python simple_diff_multi.py /path/to/data/image1.tif 
              /path/to/data/image2.tif 255 '.png' '.jpg' '.xml' 


Input: image_1 image_2 nodata_value 
  
  Where:     
        image_1       = truth image
        image_2       = test image
        nodata_value  = no data value in truth image
        fn_ignore     = tuple of path(s)/wildcard(s) to exclude from diff

        
Output: image_diff.tif, image_diff_hist.png, image_stats.csv


Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  19 September 2016
Modified: 04 November 2016


Changelog
  19 SEP 2016:  Original development.
  18 OCT 2016:  First working version.
  04 NOV 2016:  Added examples for extracting data,
                removed extension requirement,
                added ignore list option,
                modified file matching logic to be more relaxed


Prep work - extract files, keep in source dir structure:
  
  for i in ./*/*/*.gz; do tar -xzf $i --directory=$(dirname "${i}"); done


Bash call example (only if calling files of similar extensions):
  
  ias=(/path/to/data/*.ext1)
  espa=(/path/to/data/*.ext2)

  for ((i=0; i<=${#ias[@]}; i++)); do python simple_diff_multi.py ${espa[$i]} 
    ${ias[$i]} -9999 '.txt' '.xml' '.jpg' '.png'); done


List of almost always unwanted files:
  
  'png' 'jpg' 'hdf.img' 'xml' '.tar.gz' 'hdr' 'txt' 

List of sometimes unwanted files:
  
  'qa', 'BQA' 'cfmask' 'clip'

"""
##############################################################################
import sys
def do_diff(fn_mast,fn_test,mast_nodata,*args):
  ## import libraries
  try:
    
    try:
      from osgeo import gdal
    
    except ImportError:
      import gdal
    
    import os
    import copy
    import glob
    import time
    import csv
    import subprocess
    import shlex
    import numpy as np
    import matplotlib.pyplot as plt
  
  except:
    print "Could not load one or more modules."
    sys.exit(1)

  ## start timer
  t0 = time.time()
  print("\nStart time: {0}".format(time.asctime()))


  ############################################################################
  ## function to get file names
  def get_fn(id_in):
    
    ## treat netcdf or hdf cases sepcial
    if [x for x in ['.nc','.hdf'] if x in id_in]:
      id_o = id_in.split(".")[-1]
    
    ## else just read the end of the filename
    else:
      id_o = id_in.split("_")[-1:]
    #id_out = id_o[0] + "_" + id_o[1]
    #return(id_out)
    return(id_o)


  ############################################################################
  def do_cmp(fn_mast, fn_test):
    
    ## determine output directory
    #dir_out = os.path.dirname(fn_mast)
    dir_out = os.getcwd()

    ## determine scene id
    fn = os.path.basename(fn_mast)
    s_id = fn

    ## print test file names to ensure they're the same...
    fnt = os.path.basename(fn_test)

    ## get individual band names
    mast_band = get_fn(s_id)
    test_band = get_fn(fnt)
   
    if mast_band != test_band:
      print("Bands {0} and {1} are not a match! Continuing...".
                                                 format(mast_band, test_band))
      return

    print("\nTesting {0} (mast) agasint {1} (test)...".format(fn,fnt))


    ##########################################################################
    ## clip images to equivalent extent
    print("Clipping images...")
    
    ## get extents of ref image
    m_o = gdal.Open(fn_mast)
    gt = m_o.GetGeoTransform()
    ulx = gt[0]
    uly = gt[3]
    lrx = ulx + (gt[1] * m_o.RasterXSize)
    lry = uly - (gt[1] * m_o.RasterYSize)

    ## create output file
    fn_test_clip = os.path.splitext(fn_test)[0] + "_clip.tif"

    ## bulid gdal command
    cmdout = 'gdal_translate -of GTiff -projwin {0} {1} {2} {3} {4} {5}'\
             .format(str(ulx),str(uly),str(lrx),str(lry),fn_test,fn_test_clip)

    cmdout = shlex.split(cmdout)

    subprocess.Popen(cmdout)
    
    time.sleep(1) ## lazy way to make sure command finishes
   

    ##########################################################################
    ## read in binary files as GDAL datasets
    print("Reading images...")
    
    #m_o = gdal.Open(fn_mast)
    t_o = gdal.Open(fn_test_clip)

    ds_mast = m_o.GetRasterBand(1).ReadAsArray()
    ds_test = t_o.GetRasterBand(1).ReadAsArray()

    ## make nodata mask from ds_mast, mask out both rasters
    print("Masking NoData values...")
    nodata = np.zeros(np.shape(ds_mast))
    print("Target nodata value: {0}".format(mast_nodata))
    nodata[np.where((ds_mast == int(mast_nodata)) | 
                    (ds_test == int(mast_nodata)))] = int(mast_nodata)
    nodata = np.ma.masked_where(nodata == int(mast_nodata), nodata)

    ## calculate difference
    print("Calculating difference...")

    try:
      diff = ds_mast - ds_test
      diff = np.float32(np.ma.masked_where(nodata.mask == True, diff))

    except ValueError:
      print("Array sizes do not match. Saving empty CSV to indicate this...")

      c_out = open(dir_out + os.sep + s_id + "_did_not_do_analysis.csv", "wt")

      c_out.close()

      sys.exit(0)
      
    
    ## get stats for difference
    print("Doing stats...")
   
    #diff_npix     = np.sum(diff[nodata.mask == False] != 0)
    diff_npix     = np.sum(diff != 0)
    tot_pix       = np.size(diff[nodata.mask == False])
    diff_mean     = np.mean(diff)
    diff_abs_mean = np.mean(np.abs(diff))
    diff_med      = np.median(diff)
    diff_min      = np.amin(diff)
    diff_max      = np.amax(diff)
    diff_sd       = np.std(diff)
    diff_25       = np.percentile(diff, 25.)
    diff_75       = np.percentile(diff, 75.)
    diff_iqr      = diff_75 - diff_25

    try:
      pct_diff = round((float(diff_npix) / tot_pix) * 100., 6)

    except ZeroDivisionError:
      pct_diff = 100.0

    
    ##########################################################################
    ## make histogram
    if diff_mean != 0.0:
      print("Making histogram...")

      try:
        plt.hist(diff[nodata.mask == False], 255)
    
        ## define histogram parameters
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0)) ## scinot
        plt.title(s_id + " Differences")
        plt.xlabel("Value")
        plt.ylabel("Frequency")
        plt.grid(True)

        ## find source dir name (for printing output filename)
        mast_path = os.path.dirname(fn_mast).split(os.sep)[-1] + os.sep +\
                    os.path.basename(fn_mast)
        test_path = os.path.dirname(fn_test).split(os.sep)[-1] + os.sep +\
                    os.path.basename(fn_test)
        
        ## annotate plot with file names
        plt.annotate(str(mast_path) + "\n" +
                     str(test_path) + "\n",
                     fontsize=5,
                     xy=(0.01, 0.94),
                     xycoords='axes fraction')
        
        ## annotate plot with basic stats
        plt.annotate("mean diff: " + str(round(diff_mean,3)) + "\n" +
                    "abs. mean diff: " + str(round(diff_abs_mean,3)) + "\n" +
                    "# diff pixels: " + str(diff_npix) + "\n" +
                    "% diff: " + str(pct_diff) + "\n",
                    xy=(0.68, 0.8),
                    xycoords='axes fraction')

        ## write figure out to PNG
        plt.savefig(dir_out + os.sep + s_id + "_diff_hist.png",
                    bbox_inches = "tight",
                    dpi = 350)

        ## sleep here (because plots only save partially)
        time.sleep(0.5)

        plt.close()

      except ValueError:
        plt.close()
        pass


    ##########################################################################
    ## write diff image to file
    print("Writing out diff raster...")
    
    ## write diff raster
    r_out = dir_out + os.sep + s_id + "_diff.tif"
    
    ## get dims
    ncol = m_o.RasterXSize
    nrow = m_o.RasterYSize

    ## create empty raster
    target_ds = gdal.GetDriverByName('GTiff').Create(r_out, ncol, nrow, 1, 
                                                     gdal.GDT_Float32)

    ## get spatial refs
    target_ds.SetGeoTransform(m_o.GetGeoTransform())
    target_ds.SetProjection(m_o.GetProjection())

    ## define nodata value
    diff[nodata.mask == True] = int(mast_nodata)
    
    ## write array to target_ds
    target_ds.GetRasterBand(1).WriteArray(diff.data)
    target_ds.GetRasterBand(1).SetNoDataValue(int(mast_nodata))
    
    ## close file
    target_ds = None
    
    ## clean up clip band
    os.remove(fn_test_clip)


    ########################################################################  
    print("Writing out stats...")
    
    ## write stats to file
    csv_out = open(dir_out + os.sep + s_id + "_stats.csv", "wt")
    writer = csv.writer(csv_out, quoting=csv.QUOTE_NONE)
    
    ## write heade == Falser
    writer.writerow(("scene_id_mast",
                     "file_id_mast",
                     "scene_id_test",
                     "file_id_test",
                     "npix_diff",
                     "npix_total",
                     "pct_diff",
                     "mean",
                     "abs_mean",
                     "median",
                     "min",
                     "max",
                     "std_dev",
                     "25_pctile",
                     "75_pctile",
                     "iqr"))

    ## write data
    writer.writerow((s_id,
                     mast_band[0],
                     fnt,
                     test_band[0],
                     diff_npix,
                     tot_pix,
                     pct_diff,
                     diff_mean,
                     diff_abs_mean,
                     diff_med,
                     diff_min,
                     diff_max,
                     diff_sd,
                     diff_25,
                     diff_75,
                     diff_iqr))

    ## close csv file
    csv_out.close()


  ############################################################################
  ## call main function
  do_cmp(fn_mast, fn_test)
 
  ## end timer
  t1 = time.time()
  total = t1 - t0
  print("Done.")
  print("End time: {0}".format(time.asctime()))
  print("Total time: {0} minutes.".format(round(total / 60,3)))

  
##############################################################################
if __name__ == "__main__":
  
  ## error out if not enough arguments
  if len(sys.argv) < 5:
    print("Incorrect number of arguments: {0}.".format(str(len(sys.argv))))
    print('\nExample:\n python /path/to/scripts/simple_diff.py\n'
          '/path/to/data/dir_1/ /path/to/data/dir_2/ nodata_value\n'
          'ignore_values\n')
    sys.exit(1)

  else:

    ## load modules
    import multiprocessing as mp
    import glob
    import os
    import fnmatch

    ## find number of processors on system (minus one)
    proc = mp.cpu_count()-1

    ## start the processing pool
    pool = mp.Pool(processes=proc)


    ## find and sort the input files
    def find_fns(dir_in, *ignore_list):
       
      ## format ignore_list as single list of values
      igl = list(ignore_list)[0]
      
      ## allocate output file
      fns_out = []
    
      ## find all files, exclude non-testable files
      for root, dirnames, filenames in os.walk(dir_in, igl):
        
        for filename in fnmatch.filter(filenames, '*'):
          
          if [x for x in igl if x in filename]:
            pass
          
          else:
            fns_out.append(os.path.join(root, filename))
      
      return(fns_out)
     
    print("Ignore list: {0}".format((sys.argv[3:])))

    masts = sorted(find_fns(sys.argv[1], sys.argv[3:]))
    tests = sorted(find_fns(sys.argv[2], sys.argv[3:]))

    if len(masts) != len(tests):
      print('WARNING: master and test directories do not have same number\n'
            'of compoenents; results will not be consistent!\n')
    
    print(masts)
    print(tests)

    ## for each master,test file...
    for i,j in zip(masts,tests):
 
      ## assign each pair of images to it's own job
      ## apply_async() allows a new job to enter as one finishes
      r = pool.apply_async(do_diff, args=(i,j,sys.argv[3]))
    
    ## send the all the jobs out to be run
    r.get() 
