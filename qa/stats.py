"""stats.py

Purpose: get comparision results, run statistics, write out to files.
"""
import os
import csv
import numpy as np
import logging


def pct_diff_raster(ds_tband, ds_mband, diff_rast, nodata=-9999):
    """Calculate percent difference raster.

    Args:
        ds_tband <numpy.ndarray>: array of test raster
        ds_mband <numpy.ndarray>: array of master raster
        diff_rast <numpy.ndarray>: array of diff raster
    """
    # get min and max of both rasters' worth of data
    mins = []
    maxs = []  # empty variable to compare both rasters' mins
    ds_tband = np.ma.masked_where(ds_tband == nodata, ds_tband)
    ds_mband = np.ma.masked_where(ds_mband == nodata, ds_mband)

    mins.append(np.min(ds_tband))
    mins.append(np.min(ds_mband))
    rmin = np.min(mins)

    maxs.append(np.max(ds_tband))
    maxs.append(np.max(ds_mband))
    rmax = np.max(maxs)

    # make a pct diff raster
    pct_diff_raster = ((np.abs(diff_rast) / np.abs(float(rmax - rmin))) * 100)

    logging.warning("Percent difference raster created.")

    return pct_diff_raster


def img_stats(test, mast, diff_img, dir_in, fn_in, dir_out, sds_ct=0):
    """Log stats from array

    Args:
        test <str>: name of test file
        mast <str>: name of master file
        diff_img <numpy.ndarray>: image array
        dir_in <str>: directory where test data exists
        fn_in <str>: input filename (to identify csv entry)
        dir_out <str>: output directory
        sds_ct <int>: index of SDS (default=0)
    """
    diff_img = np.ma.masked_where(diff_img == 0, diff_img)

    fn_out = dir_out + os.sep + "stats.csv"
    logging.info("Writing stats for {0} to {1}.".format(fn_in, fn_out))

    file_exists = os.path.isfile(fn_out)

    with open(fn_out, "ab") as f:
        writer = csv.writer(f)

        # write header if file didn't already exist
        if not file_exists:
            writer.writerow(("dir",
                             "test_file",
                             "master_file",
                             "mean",
                             "min",
                             "max",
                             "25_percentile",
                             "75_percentile",
                             "1_percentile",
                             "99_percentile",
                             "std_dev",
                             "median"))

        writer.writerow((dir_in,
                        test + "_" + str(sds_ct),
                        mast + "_" + str(sds_ct),
                        np.mean(diff_img),
                        np.amin(diff_img),
                        np.amax(diff_img),
                        np.percentile(diff_img.compressed(), 25),
                        np.percentile(diff_img.compressed(), 75),
                        np.percentile(diff_img.compressed(), 1),
                        np.percentile(diff_img.compressed(), 99),
                        np.std(diff_img),
                        np.median(diff_img.compressed())))
