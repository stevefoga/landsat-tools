# file_io.py
import sys
import os
import logging
import tarfile
import time


class Extract:
    @staticmethod
    def unzip_gz_files(test, mast):
        """Extract files from archives in sorted order

        Args:
            test <str>: path to test .gz archive.
            mast <str>: path to master .gz archive.
        """

        print('Warning: decompressing files. Make sure you have the necessary '
              'disk space to complete this operation...\n')
        time.sleep(5)

        mast = sorted(mast)
        test = sorted(test)
        for i, j in zip(enumerate(mast), test):
            try:
                tar_mast = tarfile.open(i[1], 'r:gz')
                tar_test = tarfile.open(j, 'r:gz')
                logging.info("{0} is {1} MB...\n".
                             format(i[1], int(os.path.getsize(i[1]) >> 20)))
                logging.info("{0} is {1} MB...\n".
                             format(j, os.path.getsize(j) >> 20))

                if os.path.getsize(i[1]) == 0:
                    logging.critical("Archive {0} is of zero size!".
                                     format(i[1]))
                    sys.exit(1)

                elif os.path.getsize(j) == 0:
                    logging.critical("Archive {0} is of zero size!".
                                     format(i[j]))
                    sys.exit(1)

            except:
                logging.critical("Problem with .tar.gz file(s): {0} and {1}.".
                                 format(i[1], j))
                sys.exit(1)

            try:
                tar_mast.extractall(path=os.path.dirname(i[1]))
                tar_test.extractall(path=os.path.dirname(j))

            except:
                logging.critical("Problem extract contents from .tar.gz. file:"
                                 "{0} and {1}.".format(i[1], j))


class Find:
    @staticmethod
    def find_files(target_dir, ext):
        """Recursively find files by extension

        Args:
            target_dir <str>: path to target directory
            ext <str>: target file extension
        """
        import fnmatch

        out_files = []

        for root, dirnames, filenames in os.walk(target_dir):
            for filename in fnmatch.filter(filenames, '*' + ext):
                out_files.append(os.path.join(root, filename))

        if len(out_files) == 0:
            logging.critical("No files found in dir {0}".format(target_dir))

        return out_files

    @staticmethod
    def get_ext(*args):
        """Get unique extensions for all extracted files. Ignore .gz files.

        Args:
            *args <str>: string(s) of file extensions
        """

        exts = []
        for i in args:
            exts += [os.path.splitext(j)[1] for j in i if '.gz' not in j]

        logging.info("All extensions: {0}".format(exts))
        logging.info("Unique extensions: {0}".format(list(set(exts))))

        return list(set(exts))

    @staticmethod
    def count(fn_test, test, fn_mast, mast, ext):
        """Count number of bands inside file to decide how to iterate through
        file.

        Args:
            fn_test <str>: file name of test raster.
            test <osgeo.gdal.Dataset>: test raster
            fn_mast <str>: file name of master raster.
            mast <osgeo.gdal.Dataset>: master raster
            ext <str>: file extension of raster
        """

        def count_bands(r_name, raster):
            """Count number of bands inside raster

            Args:
                r_name <str>: file name of raster
                raster <osgeo.gdal.Dataset>: raster
            """
            try:
                from osgeo import gdal
            except ImportError:
                import gdal

            d_r = raster.RasterCount

            logging.info("Number of bands in {0}: {1}".format(r_name, d_r))

            return d_r

        def count_sds(r_name, raster):
            """Count number of SDS inside raster.

            Args:
                r_name <str>: file name of raster
                raster <osgeo.gdal.Dataset>: raster
            """
            try:
                from osgeo import gdal
            except ImportError:
                import gdal

            d_r = len(raster.GetSubDatasets())

            logging.info("Number of SDS in {0}: {1}".format(r_name, d_r))

            return d_r

        # count bands in each raster. if > 1, then handle differently
        if ext == ".img":
            # count_bands returns a 0 if there's <= 1 band in data
            d_range_test = count_bands(fn_test, test)
            d_range_mast = count_bands(fn_mast, mast)

        elif ext == ".hdf" or ext == ".nc":
            d_range_test = count_sds(fn_test, test)
            d_range_mast = count_sds(fn_mast, mast)

        else:
            d_range_test = 1
            d_range_mast = 1

        if d_range_test == 1:
            logging.info("File {0} is a singleband raster.".format(fn_test))
        else:
            logging.info("File {0} is a multiband raster.".format(fn_test))

        if d_range_mast == 1:
            logging.info("File {0} is a singleband raster.".format(fn_mast))
        else:
            logging.info("File {0} is a multiband raster.".format(fn_mast))

        if d_range_test != d_range_mast:
            logging.critical("Number of sub-bands inside raster do not match."
                             "Test: {0} | Master: {0}.".
                             format(d_range_test, d_range_mast))
            d_range = None

        else:
            d_range = d_range_test

        return d_range


class ImWrite:
    @staticmethod
    def plot_diff_image(diff_raster, fn_out, fn_type, dir_out, do_abs=False):
        """Take difference array and plot as image.

        Args:
          diff_raster <numpy.ndarray>: numpy array of values
          fn_out <str>: basename for file
          fn_type <str>: defines title of plot - "diff" or "pct_diff"
          dir_out <str>: directory where output data are being stored
        """
        import matplotlib.pyplot as plt
        import numpy as np

        # mask pixels that did not differ
        diff_raster = np.ma.masked_where(diff_raster == 0, diff_raster)

        # make output file
        im_out = dir_out + os.sep + fn_out + "_" + fn_type + ".png"

        # plot diff figure
        if do_abs:
            plt.imshow(np.abs(diff_raster), cmap='bone')
            plt.colorbar(label="Abs. Difference")
        else:
            plt.imshow(diff_raster, cmap='afmhot')
            plt.colorbar(label="Difference")

        plt.title(fn_out)
        plt.savefig(im_out, dpi=250)
        plt.close()

        logging.warning("{0} raster written to {1}.".format(fn_type, im_out))

    @staticmethod
    def plot_hist(diff_raster, fn_out, fn_type, dir_out, bins=False):
        """Take difference array and plot as histogram.

        Args:
          diff_raster <numpy.ndarray>: numpy array of values
          fn_out <str>: basename for file
          fn_type <str>: defines title of plot - "diff" or "pct_diff"
          dir_out <str>: directory where output data are being stored
          bins <int>: number of bins for histogram (default=255)
        """
        import matplotlib.pyplot as plt
        import numpy as np

        def bin_size(rast):
            """Determine bin size based upon data type.

            Args:
                rast <numpy.ndarray>: numpy array of values
            """
            dt = rast.dtype

            if '64' or '32' in dt.name:
                return 2000
            elif '16' in dt.name:
                return 1000
            elif '8' in dt.name:
                return 256
            else:
                return 50

        # mask pixels that did not differ
        diff_raster = np.ma.masked_where(diff_raster == 0, diff_raster)

        # make output file
        im_out = dir_out + os.sep + fn_out + "_" + fn_type + "_hist.png"

        # get array of values that are actually different
        diff_valid = diff_raster.compressed()

        # determine bin size
        if not bins:
            bins = bin_size(diff_raster)

        # do histogram
        plt.hist(diff_valid, bins)

        # define histogram parameters
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))  # scinot
        plt.title(fn_out + " Differences")
        plt.xlabel("Value")
        plt.ylabel("Frequency")
        plt.grid(True)

        # do basic stats
        diff_mean = np.mean(diff_raster)
        diff_sd = np.std(diff_raster)
        diff_abs_mean = np.mean(np.abs(diff_raster))
        diff_pix = len(diff_valid)
        diff_pct = (np.float(diff_pix) / np.product(np.shape(diff_raster))) \
                   * 100.0

        # annotate plot with basic stats
        plt.annotate("mean diff: " + str(round(diff_mean, 3)) + "\n" +
                     "std. dev.: " + str(round(diff_sd, 3)) + "\n" +
                     "abs. mean diff: " + str(round(diff_abs_mean, 3)) + "\n" +
                     "# diff pixels: " + str(diff_pix) + "\n" +
                     "% diff: " + str(round(diff_pct, 3)) + "\n" +
                     "# bins: " + str(bins) + "\n",
                     xy=(0.68, 0.72),
                     xycoords='axes fraction')

        # write figure out to PNG
        plt.savefig(im_out, bbox_inches="tight", dpi=350)

        plt.close()

        logging.warning("Difference histogram written to {0}.".format(im_out))


class Cleanup:
    @staticmethod
    def remove_nonmatching_files(test_fnames, mast_fnames):
        """Get rid of files that do not match so files are not incorrectly
           compared.

        Args:
           test_fnames <str>: test file
           mast_fnames <str>: master file
        """
        import itertools

        def rm_fn(fns):
            """Grab just the filename

            Args:
                fns <list>: list of paths to files
            """
            split_fnames = []
            for i in fns:
                split_fnames.append(i.split(os.sep)[-1])
            return split_fnames

        def compare_and_rm(test_fnames, mast_fnames):
            """Compare just the file names, remove non-matches, return list

            Args:
                test_fnames <str>: test file
                mast_fnames <str>: master file
            """
            fn_diffs = sorted(list(set(rm_fn(test_fnames))
                                   .difference(set(rm_fn(mast_fnames)))))

            if len(fn_diffs) > 0:
                logging.warning("Files to be removed: {0}".format(fn_diffs))

            if len(fn_diffs) == 0:
                return test_fnames

            # get only file name
            test_fn = rm_fn(test_fnames)

            rm = []
            for ii in test_fn:
                if ii in fn_diffs:
                    rm.append(False)
                else:
                    rm.append(True)

            logging.debug("remove boolean: {0}".format(rm))
            logging.debug("test_fn: {0}".format(test_fn))
            logging.debug("final list: {0}".format(list(
                itertools.compress(test_fnames, rm))))

            return list(itertools.compress(test_fnames, rm))

        test_output = compare_and_rm(test_fnames, mast_fnames)
        mast_output = compare_and_rm(mast_fnames, test_fnames)

        # if str, convert to list (other processes expect lists)
        if type(test_output) is str:
            test_output = [test_output]
        if type(mast_output) is str:
            mast_output = [mast_output]

        return test_output, mast_output

    @staticmethod
    def cleanup_files(dir_mast):
        """Clean up all test files, except for .tar.gz archives

        Args:
            dir_mast <str>: path to directory where files need to be rm'd"""
        import shutil
        import fnmatch

        print("Cleaning up files...")
        all_files = [os.path.join(dirpath, f)
                     for dirpath, dirnames, files in os.walk(dir_mast)
                     for f in fnmatch.filter(files, '*')]
        for f in all_files:
            if f.endswith(".tar.gz"):
                continue
            else:
                try:
                    os.remove(f)
                except:
                    continue

        logging.warning("Cleaned up all data files.")

        # Clean up gap mask files
        gm = [os.path.join(dirpath, f)
              for dirpath, dirnames, files in os.walk(dir_mast)
              for f in fnmatch.filter(dirnames, 'gap_mask')]
        st = [os.path.join(dirpath, f)
              for dirpath, dirnames, files in os.walk(dir_mast)
              for f in fnmatch.filter(dirnames, 'stats')]
        [shutil.rmtree(i, ignore_errors=True) for i in gm]
        [shutil.rmtree(i, ignore_errors=True) for i in st]

        logging.warning("Removed all non-archive files.")

    @staticmethod
    def rm_files(envi_files, ext):
        """Remove files from list, by specific extension

        Args:
            envi_files <list>: file names to be checked
            ext <str>: file extension to be removed"""
        out_files = [i for i in envi_files if ext not in i]

        logging.info("Skipping analysis of {0} file {1}".
                     format(ext, [i for i in envi_files if ext in i]))

        return out_files


class Read:
    @staticmethod
    def open_xml(xml_in):
        """
        Open XML and get band-specific information.

        Args:
            xml_in <str>: file path to XML
        """
        from collections import defaultdict
        import xml.etree.ElementTree as ET

        '''source: http://stackoverflow.com/questions/7684333/converting-xml-
        to-dictionary-using-elementtree'''

        def etree_to_dict(t):
            d = {t.tag: {} if t.attrib else None}
            children = list(t)
            if children:
                dd = defaultdict(list)
                for dc in map(etree_to_dict, children):
                    for k, v in dc.items():
                        dd[k].append(v)
                d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in
                             dd.items()}}
            if t.attrib:
                d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
            if t.text:
                text = t.text.strip()
                if children or t.attrib:
                    if text:
                        d[t.tag]['#text'] = text
                else:
                    d[t.tag] = text
            return d

        root = ET.parse(xml_in).getroot()

        xml_dict = etree_to_dict(root)

        bands = []
        for band in xml_dict['{http://espa.cr.usgs.gov/v2}espa_metadata'] \
                ['{http://espa.cr.usgs.gov/v2}bands'] \
                ['{http://espa.cr.usgs.gov/v2}band']:
            bands.append(band['{http://espa.cr.usgs.gov/v2}file_name'])

        if len(bands) == 0:
            return

        else:
            return bands
