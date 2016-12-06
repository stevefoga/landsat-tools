"""
make_index_band.py

Purpose: create index band for each unique scene in tile space.

Required arguments: 1) /path/to/input/files/
                    2) /path/to/output/
                    
Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  06 December 2016

Changelog:
  06 DEC 2016 - Original development.

"""
import sys

def idx_band(dir_in, dir_out):
  
  ## load modules
  import glob, os, shlex, subprocess, time
  import numpy as np
  try:
    from osgeo import gdal
  except ImportError:
    import gdal
    
  ## find unique prefixes of .tif files; use only "A1" files
  ## use sorted() to make sure Northern-most scene is first
  sr1 = sorted([fn for fn in glob.glob(dir_in + "*sr_band1.tif") if "A1" 
                in fn])
  
  ## find non-A1 files (to determine extent of output)
  tif_in = [fn for fn in glob.glob(dir_in + "*.tif") if "A1" not in fn]
  
  ## get reference image parameters (for clipping later on)
  ## get extents of ref image
  m_o = gdal.Open(tif_in[0])
  
  ## get geo params + extent of ref image
  gt = m_o.GetGeoTransform()
  
  ulx = gt[0]
  uly = gt[3]
  lrx = ulx + (gt[1] * m_o.RasterXSize)
  lry = uly - (gt[1] * m_o.RasterYSize)

  ## close file
  m_o = None

  it = 1
  
  for i in sr1:
    
    ## create output file
    fn_test_clip = os.path.splitext(i)[0] + "_clip.tif"

    ## bulid gdal command
    cmdout = 'gdal_translate -of GTiff -projwin {0} {1} {2} {3} {4} {5}'\
             .format(str(ulx),str(uly),str(lrx),str(lry),i,fn_test_clip)

    ## call gdal_translate command in shell
    cmdout = shlex.split(cmdout)
    subprocess.Popen(cmdout)
    time.sleep(1) ## lazy way to make sure command finishes
 
    ## open file
    rast = gdal.Open(fn_test_clip, gdal.GA_ReadOnly)
    rast_arr = np.array(rast.GetRasterBand(1).ReadAsArray())
    
    ## make mask of invalid data
    rast_mask = np.ma.masked_where(rast_arr == -9999, rast_arr)
    
    ## get the raster info if this is the first file
    if it == 1:
    
      ncol = rast.RasterXSize
      nrow = rast.RasterYSize
      g_trans = rast.GetGeoTransform()
      g_proj = rast.GetProjection()
      
      ## create empty grid of zeros
      grid = np.zeros((ncol, nrow))
    
    ## make mask of already assigne values
    if it > 1:
      
      used_mask = np.ma.masked_where(grid != 0, grid)
      
      ## assign 'it' value to 'grid' where 'i' is valid
      grid[np.where(~rast_mask.mask & ~used_mask.mask)] = it

    else:
      
      grid[~rast_mask.mask] = it
    
    ## close raster file
    rast = None
    
    ## clean up clip file
    os.remove(fn_test_clip)

    ## iterate it for next grid
    it = it + 1
    
  ## create output filename from input bands
  fnames = i.split(os.sep)[-1].split("_")
  fn_out = dir_out + os.sep + fnames[0] + "_" + fnames[1] + "_" + fnames[3] +\
           "_index.tif"

  ## write out grid to file
  ds = gdal.GetDriverByName('GTiff').Create(fn_out, ncol, nrow, 1, 
                                            gdal.GDT_Byte)
                                            
  ## set grid spatial reference
  ds.SetGeoTransform(g_trans)
  
  ## set grid projection
  ds.SetProjection(g_proj)
    
  ## write band
  ds.GetRasterBand(1).WriteArray(grid)
    
  ## close band (writes file)
  ds = None    
  
  
if __name__ == "__main__":
  
  if len(sys.argv) != 3:
    print(sys.argv)
    print('Incorrect number of arguments! Required:\n'
          'python make_index_band.py /path/to/input/files/\n'
          'path/to/output/')
    sys.exit(1)
    
  else:
    idx_band(sys.argv[1], sys.argv[2])
