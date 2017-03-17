"""
generate_toa_bt.py

Purpose: Generate TOA reflectance or Brightness Temperature from Level 1
          Landsat data. Works with pre-collection or Collection 1 data.

         NOTE: this was written to aid in experimental projects. The Earth
         Resources Observation and Science (EROS) Science Processing
         Architecture (ESPA; https://espa.cr.usgs.gov) provides an easier/bulk
         ordering service to create this TOA and BT data.

Inputs:   1) Landsat Level-1 bands in .tar.gz archive
Outputs:  1) TOA bands in .tar.gz archive ([original_name]_toa.tar.gz)

Tested versions: Python 2.7.x (GDAL not readily available for Python 3.x)

Example usage:
  python generate_toa_bt.py -i /path/to/your/archive.tar.gz
                            -d /path/to/your/output_directory/

Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  19 October 2016
Modified: 17 March 2017

Changelog:
  24 Oct 2016 - Original working version.
  17 Mar 2017 - PEP8 compliance, added argparse, verbose mode, cleanup

Source:
  Equations: http://landsat.usgs.gov/Landsat8_Using_Product.php
"""


def gen_toa_bt(input_gz, dir_out=False, verbose=False):
    import os
    import sys
    import tarfile
    import glob
    import time
    import numpy as np
    try:
        from osgeo import gdal
    except ImportError:
        import gdal

    if verbose:
        t0 = time.time()
        print("Start time: {0}".format(time.asctime()))

    def read_mtl(mtl):
        """
        Read MTL to dictionary.

        :param mtl: <str> path to MTL file
        :return: <dict> MTL stored in dictionary
        """
        # define fields neede from MTL
        mtl_fields = ['K1_CONSTANT_BAND',
                      'K2_CONSTANT_BAND',
                      'REFLECTANCE_MULT_BAND',
                      'REFLECTANCE_ADD_BAND',
                      'RADIANCE_MULT_BAND',
                      'RADIANCE_ADD_BAND',
                      'SUN_ELEVATION']

        # open MTL file
        with open(mtl) as f:
            # read for specific contents, put into dict
            mtl_file = {}

            for text in f:
                out = [text for t in mtl_fields if t in text]
                if out:
                    # split the key and value, use strip() to rm whitespace
                    mtl_key = out[0].split(" = ")[0].strip()
                    mtl_value = out[0].split(" = ")[1].split(",\n")[0].strip()

                    # put key in mtl dict, assign value
                    mtl_file[mtl_key] = float(mtl_value)

        return mtl_file

    def xmus(mtl_file):
        """
        Get cosine of solar zenith angle (xmus == name from ESPA TOA code)

        :param mtl_file: <dict> MTL file read in as dict
        :return: <float> cosine of solar zenith angle
        """
        try:
            c_sza = np.cos(np.deg2rad(90 - float(mtl_file['SUN_ELEVATION'])))

            if verbose:
                print("SUN_ELEVATION: {0}".format(str(mtl_file[
                                                          'SUN_ELEVATION'])))
                print("cosine sza: {0}".format(str(c_sza)))

            return c_sza

        except KeyError:
            print("Could not find SUN_ELEVATION from MTL.")
            sys.exit(1)

    def band_by_sensor(landsat_8, bnds):
        """
        Assign bands to a dictionary

        :param landsat_8: <bool> whether or not the scene is L8
        :param bnds: <list> list of data bands
        :return: <dict> name of each band in dict
        """
        b_c = {}

        if landsat_8:
            b_c['ca'] = [b for b in bnds if "_B1." in b][0]
            b_c['blue'] = [b for b in bnds if "_B2." in b][0]
            b_c['green'] = [b for b in bnds if "_B3." in b][0]
            b_c['red'] = [b for b in bnds if "_B4." in b][0]
            b_c['nir'] = [b for b in bnds if "_B5." in b][0]
            b_c['swir1'] = [b for b in bnds if "_B6." in b][0]
            b_c['swir2'] = [b for b in bnds if "_B7." in b][0]
            b_c['cir'] = [b for b in bnds if "_B9." in b][0]
            b_c['therm'] = [b for b in bnds if "_B10." in b][0]
            b_c['therm2'] = [b for b in bnds if "_B11." in b][0]

        else:
            b_c['blue'] = [b for b in bnds if "_B1." in b][0]
            b_c['green'] = [b for b in bnds if "_B2." in b][0]
            b_c['red'] = [b for b in bnds if "_B3." in b][0]
            b_c['nir'] = [b for b in bnds if "_B4." in b][0]
            b_c['swir1'] = [b for b in bnds if "_B5." in b][0]
            b_c['swir2'] = [b for b in bnds if "_B7." in b][0]
            b_c['therm'] = [b for b in bnds if "_B6." in b][0]

            if verbose:
                print("Thermal band: {0}".format(b_c['therm']))

        return b_c

    def read_bands(band_in):
        """
        Read band data in with GDAL.

        :param band_in: <str> path to image file
        :return: <np.ndarray> image array
        """
        rast = gdal.Open(band_in, gdal.GA_ReadOnly)

        return np.array(rast.GetRasterBand(1).ReadAsArray())

    def get_band_no(fn):
        """
        Find the band number (for output file naming)

        :param fn: <str> path to input band
        :return: <str> band number
        """
        # get band name
        fn = os.path.basename(fn)

        # find band number
        band = fn.split(".TIF")[0][-3:]
        if "_" in band:  # C1 uses underscores in file names
            band = band.split("_")[1]

        return band.split("B")[-1]

    def get_geo_params(fn):
        """
        Get geo params

        :param fn: <str> path to input band
        :return: <gdal> GDAL object
        """
        return gdal.Open(fn, gdal.GA_ReadOnly)

    def spec_rad(band, m_l, a_l):
        """
        Get TOA (spectral) radiance

        :param band: <np.ndarray> image data
        :param m_l: <float> multiplicative scaling factor
        :param a_l: <float> additive scaling factor
        :return: <np.ndarray> spectral radiance band
        """
        return (float(m_l) * np.asfarray(band)) + a_l

    def do_bt(band_in, k1, k2, ml, al):
        """
        Compute brightness temperature.

        :param band_in: <str> file name of data band
        :param k1: <float>
        :param k2: <float>
        :param ml: <float>
        :param al: <float>
        :return: <np.ndarray> brightness temp band
        """
        # read bands
        t_band = read_bands(band_in)

        # mask out nodata
        mask_band = np.ma.masked_where(t_band == 0, t_band)

        # calculate spectral radiance
        s_rad = spec_rad(t_band, ml, al)

        # calculate bt
        btemp = float(k2) / np.log((float(k1) / np.asfarray(s_rad)) + 1)

        return np.ma.masked_where(mask_band, btemp)

    def toa_params(fn_in, mtl):
        """
        Get multiplicative and additive rescaling refl. from MTL

        :param fn_in: <str> input file name
        :param mtl: <dict> MTL read into dictionary
        :return: <float, float> mult and add variables
        """
        # get mp and ap with band numbers
        mult_b = float(mtl["REFLECTANCE_MULT_BAND_" + get_band_no(fn_in)])
        add_b = float(mtl["REFLECTANCE_ADD_BAND_" + get_band_no(fn_in)])

        if verbose:
            print("REFLECTANCE_MULT_BAND_{0}: {1}".format(str(get_band_no(
                fn_in)), str(mult_b)))

            print("REFLECTANCE_ADD_BAND_{0}: {1}".format(str(get_band_no(
                fn_in)), str(add_b)))

        return mult_b, add_b

    def rad_params(fn_in, mtl_file):
        """
        Get multiplicative and additive rescaling radiance from MTL

        :param fn_in: <str> input file name
        :param mtl_file: <dict> MTL read into dictionary
        :return: <float, float> mult and add variables
        """
        # get ml and al with band numbers
        mult_r = float(mtl_file["RADIANCE_MULT_BAND_" + get_band_no(fn_in)])
        add_r = float(mtl_file["RADIANCE_ADD_BAND_" + get_band_no(fn_in)])

        if verbose:
            print("RADIANCE_MULT_BAND_{0}: {1}".format(str(get_band_no(fn_in)),
                                                       str(mult_r)))

            print("RADIANCE_ADD_BAND_{0}: {1}".format(str(get_band_no(fn_in)),
                                                      str(add_r)))

        return mult_r, add_r

    def bt_params(fn_in, mtl):
        """
        Get K1 and K2 constants from MTL

        :param fn_in: <str> data band name
        :param mtl: <dict> MTL contents read into dictionary
        :return: <float, float> K1 and K2 constants
        """
        if "B10" in fn_in:
            k1 = float(mtl['K1_CONSTANT_BAND_10'])
            k2 = float(mtl['K2_CONSTANT_BAND_10'])

            if verbose:
                print("B10 K1: {0}".format(str(k1)))
                print("B10 K2: {0}".format(str(k2)))

        elif "B11" in fn_in:
            k1 = float(mtl['K1_CONSTANT_BAND_11'])
            k2 = float(mtl['K2_CONSTANT_BAND_11'])

            if verbose:
                print("B11 K1: {0}".format(str(k1)))
                print("B11 K2: {0}".format(str(k2)))

        elif "B6." in fn_in:
            k1 = float(mtl['K1_CONSTANT_BAND_6'])
            k2 = float(mtl['K2_CONSTANT_BAND_6'])

            if verbose:
                print("B6 K1: {0}".format(str(k1)))
                print("B6 K2: {0}".format(str(k2)))

        else:
            print("Could not find thermal constants!")
            print("Operating on file {0}".format(str(i)))
            sys.exit(1)

        return k1, k2

    def do_toa(band_in, m_p, a_p, c_sza):
        """
        Process data to TOA reflectance

        :param band_in: <str> name of data band
        :param m_p: <float> mult factor
        :param a_p: <float> add factor
        :param c_sza: <float> cosine of solar zenith angle
        :return: <np.ndarray> TOA reflectance data band
        """
        # read bands
        o_band = read_bands(band_in)

        # mask out nodata
        mask_band = np.ma.masked_where(o_band == 0, o_band)

        # calculate toa
        toar = (float(m_p) * np.asfarray(o_band)) + a_p

        # do sun angle correction
        toar = np.asfarray(toar) / float(c_sza)

        # mask out nodata
        return np.ma.masked_where(mask_band, toar)

    def write_raster(base_name, data_out, lsat_coll):
        """
        Write raster out to new file.

        :param base_name: <str> base file name
        :param data_out: <np.ndarray> array of data to write to file
        :param lsat_coll: <bool> pre-collection (False) or C1 (True)
        :return:
        """
        # call function to get band number
        bnd_no = get_band_no(base_name)

        # call function to get geo parameters for this band
        geo_params = get_geo_params(base_name)

        # make output file name
        fpath, fname = os.path.split(base_name)

        if lsat_coll:
            # if collection data, grab specific characters
            l_id = fname[0:40] + "_toa_band" + bnd_no

        else:
            # if pre-collection data, grab specific characters
            l_id = fname[0:21] + "_toa_band" + bnd_no

        # create output filename
        fn_out = fpath + os.sep + l_id + ".tif"

        # get band dimensions
        ncol = geo_params.RasterXSize
        nrow = geo_params.RasterYSize

        # create empty raster
        ds = gdal.GetDriverByName('GTiff').Create(fn_out, ncol, nrow, 1,
                                                  gdal.GDT_Int16)

        # set grid spatial reference
        ds.SetGeoTransform(geo_params.GetGeoTransform())

        # set grid projection
        ds.SetProjection(geo_params.GetProjection())

        # set nodata value
        ds.GetRasterBand(1).SetNoDataValue(-9999)

        # write band
        ds.GetRasterBand(1).WriteArray(data_out)

        # close band (writes file)
        ds = None

    def make_tarfile(output_filename, source_files):
        """
        Make .tar.gz with output TOA file(s)

        :param output_filename: <str> path + filename for output archive
        :param source_files: <list> files to be archived
        :return:
        """
        with tarfile.open(output_filename, "w:gz") as tar:
            for s in source_files:
                tar.add(s, arcname=os.path.basename(s))

    def del_file(a):
        """
        Clean up files.

        :param a: <list> input files
        :return:
        """
        try:
            for r in a:
                os.remove(r)
        except OSError:
            pass

    '''
    file i/o
    '''
    # untar files
    t_o = tarfile.open(input_gz, 'r:gz')

    print("Extracting files...")

    try:
        t_o.extractall(path=os.path.dirname(input_gz))
    except:
        print("Problem extracting .tar.gz file {0}".format(input_gz))
        sys.exit(1)

    # find all band files
    print("Finding bands...")
    dir_in = os.path.dirname(input_gz)

    bands_1 = glob.glob(dir_in + os.sep + "*_B[1-9]*")  # bands 1-9
    bands_2 = glob.glob(dir_in + os.sep + "_*B[0-1][0-1]*")  # bands 10-11
    bands = bands_1 + bands_2

    # find MTL file
    mtl_f = glob.glob(dir_in + os.sep + "*MTL.txt")[0]

    # get MTL components
    mtl = read_mtl(mtl_f)

    # get cosine of solar zenith angle (for TOA calc)
    cos_sza = xmus(mtl)

    # get base name of first band
    fn = os.path.basename(bands[0])

    # if Collection 1 data, check first four digits for sensor
    if fn[2] == '0':
        lsat_coll = True

        if fn[2:4] == '08':  # Landsat 8
            band_col = band_by_sensor(True, bands)
        else:
            band_col = band_by_sensor(False, bands)

    else:
        lsat_coll = False

        if fn[2] == '8':  # Landsat 8
            band_col = band_by_sensor(True, bands)
        else:
            band_col = band_by_sensor(False, bands)

    # separate thermal vs. optical bands
    therm_col = {}
    opt_col = {}

    for key in band_col:
        if 'therm' in key:
            therm_col[key] = band_col[key]
        else:
            opt_col[key] = band_col[key]

    '''
    top of atmosphere (toa)
    '''
    print("Calculating TOA...")
    it = 0
    for i in opt_col:
        # get toa params
        mp, ap = toa_params(opt_col[i], mtl)

        # get toa
        toa_out = do_toa(opt_col[i], mp, ap, cos_sza)

        # rescale band
        toa_out = np.round(toa_out * 10000, 0)
        toa_out = toa_out.astype('int16')

        # set nodata value
        toa_out[toa_out.mask] = -9999

        # write out to raster
        write_raster(opt_col[i], toa_out, lsat_coll)

        it += 1
        print("TOA calculation {0} of {1} complete."
              .format(it, len(opt_col)))

    '''
    brightness temp (bt)
    '''
    it = 0
    for i in therm_col:
        # get radiance params
        ml, al = rad_params(therm_col[i], mtl)

        # get bt params
        k1, k2 = bt_params(therm_col[i], mtl)

        # get bt
        bt_out = do_bt(therm_col[i], k1, k2, ml, al)

        # rescale band
        bt_out = np.round(bt_out * 10, 0)
        bt_out = bt_out.astype('int16')

        # set nodata value
        bt_out[bt_out.mask] = -9999

        # write out to raster
        write_raster(therm_col[i], bt_out, lsat_coll)

        it += 1
        print("BT calculation {0} of {1} complete."
              .format(it, (len(therm_col))))

    '''
    archive, clean up files
    '''
    if dir_out:
        output_gz = dir_out + \
                    os.path.basename(input_gz).split(".tar.gz")[0] + \
                    "_toa.tar.gz"

    else:
        output_gz = input_gz.split(".tar.gz")[0] + "_toa.tar.gz"

    toa_out = glob.glob(dir_in + os.sep + "*.tif")

    if len(toa_out) > 0:

        # put files into archive
        print("Adding data to .tar.gz archive...")
        make_tarfile(output_gz, toa_out)

        print("File location: {0}".format(str(output_gz)))

        # clean up everything else (txt, tif, TIF, jpg, png)
        print("Cleaning up files...")

        del_file(toa_out)
        del_file(glob.glob(dir_in + os.sep + "*.txt"))
        del_file(glob.glob(dir_in + os.sep + "*.png"))
        del_file(glob.glob(dir_in + os.sep + "*.jpg"))
        del_file(glob.glob(dir_in + os.sep + "*.TIF"))

    else:
        print("No TOA or BT files found!")
        sys.exit(1)

    '''
    end timer, print results
    '''
    if verbose:
        t1 = time.time()
        total = t1 - t0
        print("End time: {0}".format(time.asctime()))
        print("Total time: {0} minutes.".format(round(total / 60, 3)))

    print("Done.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate TOA reflectance or Brightness Temperature from '
                    'Level 1 Landsat data. Works with Pre-Collection or '
                    'Collection 1 data.')

    req_named = parser.add_argument_group('Required named arguments')

    req_named.add_argument('-i', action='store', dest='input_gz', type=str,
                           help='Level-1 data archive', required=True)

    req_named.add_argument('-d', action='store', dest='dir_out', type=str,
                           help='Output directory (default=input dir',
                           required=False)

    req_named.add_argument('--verbose', action='store', dest='verbose',
                           required=False)

    arguments = parser.parse_args()

    gen_toa_bt(**vars(arguments))
