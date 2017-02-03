# qa_images.py
import logging
import numpy as np


def do_diff(test, mast, nodata=False):
    """Do image diff, break if the grids are not the same size.

    Args:
        test <numpy.ndarray>: array of test raster
        mast <numpy.ndarray>: array of master raster
    """
    if nodata:
        test = np.ma.masked_where(test == nodata, test)
        mast = np.ma.masked_where(mast == nodata, mast)

        logging.info("Making nodata value {0} from diff calc.".format(nodata))

    try:
        ## TODO: Figure out why some bands cannot be compared correctly.
        diff = test.astype(np.float) - mast.astype(np.float)

        return diff

    except (ValueError, AttributeError, TypeError) as e:
        logging.warning("Error: {0}".format(e))

        return False


def call_stats(rast_arr, fn_out, dir_out, rast_num=0):
    """Call stats function(s) if data are valid

    Args:
        rast_arr <numpy.ndarray>: array of target raster
        fn_out <str>: file path of image
        dir_out <str>: path to output directory
        rast_num <int>: individual number of image (default=0)
        nodata <int>: no data value (default=-9999)
    """
    import os
    import stats
    from file_io import ImWrite

    if type(rast_arr) is np.ndarray or \
                    type(rast_arr) is np.ma.core.MaskedArray:
        if np.any(rast_arr != 0):
            logging.warning("Image difference found!")
            # find file name (for saving plot)
            fout = fn_out.split(os.sep)[-1]

            # do stats of difference
            stats.img_stats(rast_arr, os.path.dirname(fn_out), fout, dir_out,
                            rast_num)

            # plot diff image
            ImWrite.plot_diff_image(rast_arr, fout, "diff_" + str(rast_num),
                                    dir_out)

            # plot abs diff image
            ImWrite.plot_diff_image(rast_arr, fout, "abs_diff_" +
                                    str(rast_num), dir_out, do_abs=True)

            # plot diff histograms
            ImWrite.plot_hist(rast_arr, fout, "diff_" + str(rast_num), dir_out)

        else:
            logging.info("Binary data match.")

    else:
        logging.warning("Target raster is not a valid numpy array or numpy "
                        "masked array. Cannot run statistics!")


class ArrayImage:
    @staticmethod
    def check_images(test, mast):
        """Read in a generic (non-geographic) image, like JPEG, and do a diff
        Return diff raster if actually different

        Args:
            test <str>: path to test image
            mast <str>: path to master image
        """
        try:
            from scipy.misc import imread
        except ImportError:
            from scipy.ndimage import imread

        # read images
        try:
            test_im = imread(test)
            mast_im = imread(mast)
        except ImportError:
            logging.warning("Likely missing Python Image Library (PIL).")

            # try Scikit Image
            from skimage.io import imread
            try:
                mast_im = imread(mast)
                test_im = imread(test)
            except (ValueError, TypeError, ImportError):
                logging.warning("Not able to open image with skimag.io. Likely"
                                " missing image library.")
                return None

        # check diff
        try:
            diff_im = do_diff(test_im, mast_im)

            if len(np.nonzero(diff_im)) > 3:
                logging.error("Values differ between {0} and {1}.".
                              format(test, mast))
                return diff_im

            else:
                logging.info("Values equivalent between {0} and {1}.".
                             format(test, mast))
                return None

        except ValueError:
            logging.error("Image {0} and {1} are not the same dimensions.".
                          format(test, mast))


class GeoImage:
    @staticmethod
    def check_images(test, mast, dir_out, ext):
        """Compare the test and master images, both for their raw contents and
        geographic parameters. If differences exist, produce diff plot + CSV
        stats file.

        Args:
            test <str>: path to test image
            mast <str>: path to master image
            dir_out <str>: path to output directory
            ext <str>: file extension
        """
        import os
        from image_io import RasterIO, RasterCmp
        from file_io import Cleanup, Find
        import logging

        print("Checking {0} files...".format(ext))

        # clean up non-matching files
        test, mast = Cleanup.remove_nonmatching_files(test, mast)

        # make sure there are actually files to check
        if mast is None or test is None:
            logging.error("No {0} files to check in test and/or mast "
                          "directories.".format(ext))
            return False

        # do other comparison checks, return stats + plots if diffs exist
        for i, j in zip(test, mast):

            logging.info("Checking Test {0} against Master {1}".format(i, j))
            # Open each raster
            ds_test = RasterIO.open_raster(i)
            ds_mast = RasterIO.open_raster(j)

            # Compare various raster parameters
            status = []
            status.append(RasterCmp.compare_proj_ref(ds_test, ds_mast))
            status.append(RasterCmp.compare_geo_trans(ds_test, ds_mast))
            status.append(RasterCmp.extent_diff_cols(ds_test, ds_mast))
            status.append(RasterCmp.extent_diff_rows(ds_test, ds_mast))

            # If any above tests fail, go to next iteration
            if any(stat == False for stat in status):
                continue

            # Count number of sub-bands in the files
            d_range = Find.count(i, ds_test, j, ds_mast, ext)

            # if sub-bands exist, read them one-by-one and do diffs + stats
            if d_range > 1:
                for ii in range(0, d_range):
                    # Get the first band from each raster
                    if ext == ".img":
                        logging.info("Reading sub-band {0} from .img {1}...".
                                     format(ii, i))
                        ds_tband = RasterIO.read_band_as_array(ds_test, ii)
                        ds_mband = RasterIO.read_band_as_array(ds_mast, ii)
                    else:
                        logging.info("Reading .hdf/.nc SDS {0} from file "
                                     "{0}...".format(ii, i))
                        sds_tband = RasterIO.open_raster(
                            RasterIO.get_sds(ds_test)[ii][0])
                        sds_mband = RasterIO.open_raster(
                            RasterIO.get_sds(ds_mast)[ii][0])
                        ds_tband, t_nd = RasterIO.read_band_as_array(sds_tband)
                        ds_mband, m_nd = RasterIO.read_band_as_array(sds_mband)

                    # do diff
                    if type(t_nd) == type(None):
                        diff = do_diff(ds_tband, ds_mband)
                    else:
                        diff = do_diff(ds_tband, ds_mband, nodata=int(t_nd))

                    # call stats functions to write out results/plots/etc.
                    call_stats(diff, i, dir_out, rast_num=ii)

            else:  # else it's a singleband raster
                logging.info("Reading {0}...".format(i))

                # read in band as array
                ds_tband, t_nd = RasterIO.read_band_as_array(ds_test)
                ds_mband, m_nd = RasterIO.read_band_as_array(ds_mast)

                # do diff
                if type(t_nd) == type(None):
                    diff = do_diff(ds_tband, ds_mband)
                else:
                    diff = do_diff(ds_tband, ds_mband, nodata=int(t_nd))

                # call stats functions to write out results/plots/etc.
                call_stats(diff, i, dir_out)
