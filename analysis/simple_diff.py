"""
simple_diff.py

Purpose: Diff two image files, and output diff image + statistics.

Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  19 September 2016
Modified: 23 December 2016
"""
import sys


def find_files(target_dir, ext):
    """Recursively find files by extension

    Args:
        target_dir <str>: path to target directory
        ext <str>: target file extension
    """
    import os
    import fnmatch

    out_files = []

    for root, dirnames, filenames in os.walk(target_dir):
        for filename in fnmatch.filter(filenames, '*' + ext):
            out_files.append(os.path.join(root, filename))

    return out_files

def get_fn(id_in):
    """Re-construct file names for the stats csv file.

    Args:
        id_in <str>: file name.
    """

    id_o = id_in.split("_")[-2:]
    id_out = id_o[0] + "_" + id_o[1]

    return id_out

def do_cmp(fn_mast, fn_test, mast_nodata, dir_out, ignore_fn, skip_fr):
    """
    Args:
        fn_mast <str>: master image file
        fn_test <str>: test image file
        mast_nodata <int>: nodata value for master and test files
        ext_1 <str>: file extension of master image file(s)
        ext_2 <str>: file extension of test image file(s)
        dir_out <str>: path to output directory (default=current working dir)
        ignore_fn <bool>: do not bother matching files (default=False)
        skip_fr <bool>: skip making full-res diff image (default=False)
    return:
        .csv file of statistics
        .png file of histogram
        .tif file of full-res difference (optional)
    """
    try:
        from osgeo import gdal

    except ImportError:
        import gdal

    import os
    import csv
    import shlex
    import subprocess
    import numpy as np
    import matplotlib.pyplot as plt

    # determine scene id
    fn = os.path.basename(fn_mast)
    s_id = fn

    ## print test file names to ensure they're the same...
    fnt = os.path.basename(fn_test)

    # get individual band names
    mast_band = get_fn(s_id)
    test_band = get_fn(fnt)

    if not ignore_fn:
        if mast_band != test_band:
            print("Bands {0} and {1} are not a match! Continuing...".
                  format(mast_band, test_band))
            return

    print("\nTesting {0} (mast) against {1} (test)...".format(fn, fnt))

    # clip images to equivalent extent
    print("Clipping images...")

    # get extents of ref image
    m_o = gdal.Open(fn_mast)
    gt = m_o.GetGeoTransform()
    ulx = gt[0]
    uly = gt[3]
    lrx = ulx + (gt[1] * m_o.RasterXSize)
    lry = uly - (gt[1] * m_o.RasterYSize)

    # create output file
    fn_test_clip = os.path.splitext(fn_test)[0] + "_clip.tif"

    # bulid gdal command
    cmdout = 'gdal_translate -of GTiff -projwin {0} {1} {2} {3} {4} {5}' \
        .format(str(ulx), str(uly), str(lrx), str(lry), fn_test,
                fn_test_clip)

    # call out to command line
    subprocess.check_call(shlex.split(cmdout))

    # read in binary files as GDAL datasets
    print("Reading images...")

    t_o = gdal.Open(fn_test_clip)

    ds_mast = m_o.GetRasterBand(1).ReadAsArray()
    ds_test = t_o.GetRasterBand(1).ReadAsArray()

    # make nodata mask from ds_mast, mask out both rasters
    print("Masking NoData values...")
    nodata = np.zeros(np.shape(ds_mast))

    print("Target nodata value: {0}".format(mast_nodata))
    nodata[np.where((ds_mast == int(mast_nodata)) |
                    (ds_test == int(mast_nodata)))] = int(mast_nodata)
    nodata = np.ma.masked_where(nodata == int(mast_nodata), nodata)

    # calculate difference
    print("Calculating difference...")

    try:
        diff = ds_mast - ds_test
        diff = np.float32(np.ma.masked_where(nodata.mask == True, diff))

    except ValueError:
        print(
        "Array sizes do not match. Saving empty CSV to indicate this...")

        c_out = open(dir_out + os.sep + s_id + "_did_not_do_analysis.csv",
                     "wt")

        c_out.close()

        sys.exit(0)

    # get stats for difference
    print("Doing stats...")

    diff_npix = np.sum(diff != 0)
    tot_pix = np.size(diff[nodata.mask == False])
    diff_mean = np.mean(diff)
    diff_abs_mean = np.mean(np.abs(diff))
    diff_med = np.median(diff)
    diff_min = np.amin(diff)
    diff_max = np.amax(diff)
    diff_sd = np.std(diff)
    diff_25 = np.percentile(diff, 25)
    diff_75 = np.percentile(diff, 75)
    diff_iqr = diff_75 - diff_25

    try:
        pct_diff = round((float(diff_npix) / tot_pix) * 100., 3)

    except ZeroDivisionError:
        pct_diff = 100.0

    # make histogram
    print("Making histogram...")
    try:
        plt.hist(diff[nodata.mask == False], 255)

        # define histogram parameters
        plt.ticklabel_format(style='sci', axis='y',
                             scilimits=(0, 0))  # sci. notation enabled
        plt.title(s_id + " Differences")
        plt.xlabel("Value")
        plt.ylabel("Frequency")
        plt.grid(True)

        # annotate plot with basic stats
        plt.annotate("mean diff: " + str(round(diff_mean, 3)) + "\n" +
                     "abs. mean diff: " + str(
            round(diff_abs_mean, 3)) + "\n" +
                     "# diff pixels: " + str(diff_npix) + "\n" +
                     "% diff: " + str(pct_diff) + "\n",
                     xy=(0.7, 0.8),
                     xycoords='axes fraction')

        # write figure out to PNG
        plt.savefig(dir_out + os.sep + s_id + "_diff_hist.png",
                    bbox_inches="tight",
                    dpi=350)

        plt.close()

    except ValueError:
        pass

    if not skip_fr:
        # write diff image to file
        print("Writing out diff raster...")

        # write diff raster
        r_out = dir_out + os.sep + s_id + "_diff.tif"

        # get dims
        ncol = m_o.RasterXSize
        nrow = m_o.RasterYSize

        # create empty raster
        target_ds = gdal.GetDriverByName('GTiff').Create(r_out, ncol, nrow, 1,
                                                         gdal.GDT_Float32)

        # get spatial refs
        target_ds.SetGeoTransform(m_o.GetGeoTransform())
        target_ds.SetProjection(m_o.GetProjection())

        # define nodata value
        diff[nodata.mask == True] = int(mast_nodata)

        # write array to target_ds
        target_ds.GetRasterBand(1).WriteArray(diff.data)
        target_ds.GetRasterBand(1).SetNoDataValue(int(mast_nodata))

        # close files
        target_ds = None
        t_o = None
        m_o = None

    # clean up clip band
    os.remove(fn_test_clip)

    print("Writing out stats...")

    # write stats to file
    csv_out = open(dir_out + os.sep + s_id + "_stats.csv", "wb")
    writer = csv.writer(csv_out, quoting=csv.QUOTE_NONE)

    # write header == False
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

    # write data
    writer.writerow((s_id,
                     mast_band,
                     fnt,
                     test_band,
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

    # close csv file
    csv_out.close()


def main(fn_mast, fn_test, mast_nodata, ext_1, ext_2, dir_out, ignore_fn,
         skip_fr):
    import time

    # start timer
    t0 = time.time()
    print("\nStart time: {0}".format(time.asctime()))

    # find and sort the input files
    masts = sorted(find_files(fn_mast, ext_1))
    tests = sorted(find_files(fn_test, ext_2))

    it = 0
    for i, j in zip(masts, tests):
        do_cmp(i, j, mast_nodata, dir_out, ignore_fn, skip_fr)

        it += 1
        print('\n{0} of {1} complete.\n'.format(str(it), str(len(masts))))

    print("Files written to {0}.".format(dir_out))

    # end timer
    t1 = time.time()
    total = t1 - t0
    print("Done.")
    print("End time: {0}".format(time.asctime()))
    print("Total time: {0} minutes.".format(round(total / 60, 3)))


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser()

    #parser.set_defaults(func=main)

    parser.add_argument('-m', action='store', dest='fn_mast', type=str,
                        help='Master directory of images.', required=True)

    parser.add_argument('-t', action='store', dest='fn_test', type=str,
                        help='Test directory of images.', required=True)

    parser.add_argument('-n', action='store', dest='mast_nodata', type=int,
                        help='NoData value.', required=True)

    parser.add_argument('-et', action='store', dest='ext_1', type=str,
                        help='Extension of test image(s).', required=True)

    parser.add_argument('-em', action='store', dest='ext_2', type=str,
                        help='Extension of master image(s).', required=True)

    parser.add_argument('-o', action='store', dest='dir_out', type=str,
                        default=os.getcwd(),
                        help='Output directory. Default = current working '
                             'directory.', required=False)

    parser.add_argument('--ignore-fnames', action='store', dest='ignore_fn',
                        type=str, default=False,
                        help='Do not match file names.', required=False)

    parser.add_argument('--skip-fullres', action='store', dest='skip_fr',
                        type=str, default=False,
                        help='Skip creation of full-resolution diff images',
                        required=False)

    arguments = parser.parse_args()

    main(**vars(arguments))
