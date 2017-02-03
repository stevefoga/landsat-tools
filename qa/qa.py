"""
qa.py

Purpose: Perform QA on georeferenced images and associated metadata. Designed
         originally to support the Earth Resources Observation and Science
         (EROS) Science Processing Architecture
         (ESPA; https://espa.cr.usgs.gov/.)
         Extract and clean up data automatically (if necessary.)
         Report results in logfile, CSV and plots.

Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  21 December 2016
Modified: 02 February 2017

Changelog:
    21 Dec 2016: Original development.
    12 Jan 2017: Fixed errors, formatting.
    02 Feb 2017: Added switch for archived or non-archived inputs; modified
                 stats output on plots; fixed nodata filtering for histograms;
                 wrote XML parsing code (but not useage of said output); fixed
                 file removal logic in file_io.py

Todo:
    1) Utilize XML for nodata, file names, etc.

"""

def qa_data(dir_mast, dir_test, dir_out, archive=True, use_xml=False,
            verbose=False):
    """Function to check files and call appropriate QA module(s)

    Args:
        dir_mast <str>: path to master directory
        dir_test <str>: path to test directory
        dir_out <str>: path to QA output directory
        archive <bool>: cleanup, extract from archives, else assume dirs
            (default = True)
        use_xml <bool>: use XML for filenames instead of parsing dirs
            (default = False)
        verbose <bool>: enable/disable verbose logging (default = False)
    """
    import sys
    import os
    from file_io import Extract, Find, Cleanup
    from qa_images import GeoImage
    from qa_metadata import MetadataQA
    import logging
    import time

    # start timing code
    t0 = time.time()

    # create output dir if it doesn't exist
    if not os.path.exists(dir_out):
        os.mkdir(dir_out)

    # initiate logger
    if verbose:
        log_out = dir_out + os.sep + "log_" + time.strftime("%Y%m%d-%I%M%S") \
            + "_verbose.log"
        logging.basicConfig(filename=log_out,
                            level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(name)s - \
                            %(message)s')

    else:
        log_out = dir_out + os.sep + "log_" + time.strftime("%Y%m%d-%I%M%S") \
                  + ".log"
        logging.basicConfig(filename=log_out,
                            level=logging.WARNING,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    if archive:
        # do initial cleanup of input directories
        Cleanup.cleanup_files(dir_mast)
        Cleanup.cleanup_files(dir_test)

        # create output directory if it doesn't exist
        if not os.path.exists(dir_out):
            os.makedirs(dir_out)

        # read in .tar.gz files
        test_files = Find.find_files(dir_test, ".gz")
        mast_files = Find.find_files(dir_mast, ".gz")

        # Extract files from archive
        Extract.unzip_gz_files(test_files, mast_files)

    # TODO: Implement checking file names with XML.
    # TODO: Ensure compatibility with NetCDF, HDF files.

    # find only the deepest dirs
    test_dirs = [r for r, d, f in os.walk(dir_test) if not d]
    mast_dirs = [r for r, d, f in os.walk(dir_mast) if not d]

    if len(test_dirs) != len(mast_dirs):
        logging.critical("Directory structure of Master differs from Test.")
        sys.exit(1)

    for i in range(0, len(test_dirs)):

        # Find extracted files
        all_test = Find.find_files(test_dirs[i], ".*")
        all_mast = Find.find_files(mast_dirs[i], ".*")

        # Find unique file extensions
        exts = Find.get_ext(all_test, all_mast)

        for j in exts:

            logging.info("Finding {0} files...".format(j))
            test_f = Find.find_files(test_dirs[i], j)
            mast_f = Find.find_files(mast_dirs[i], j)

            logging.info("Performing QA on {0} files located in {1}".
                         format(j, dir_test))
            logging.info("Test files: {0}".format(test_f))
            logging.info("Mast files: {0}".format(mast_f))

            # remove any _hdf.img files found with .img files
            if j == ".img":
                test_f = Cleanup.rm_files(test_f, "_hdf.img")
                mast_f = Cleanup.rm_files(mast_f, "_hdf.img")

            if (j.lower() == ".txt" or j.lower() == ".xml"
                or j.lower() == ".gtf" or j.lower() == ".hdr" or
                j.lower() == ".stats"):
                MetadataQA.check_text_files(test_f, mast_f, j)

            elif j.lower() == ".jpg":
                MetadataQA.check_jpeg_files(test_f, mast_f, dir_out)

            elif len(j) == 0:
                continue

            else:
                GeoImage.check_images(test_f, mast_f, dir_out, j)

    if archive:
        # Clean up files
        Cleanup.cleanup_files(dir_mast)
        Cleanup.cleanup_files(dir_test)

    # end timing
    t1 = time.time()
    m, s = divmod(t1 - t0, 60)
    h, m = divmod(m, 60)
    logging.warning("Total runtime: {0}h, {1}m, {2}s.".format(h, round(m, 3),
                                                              round(s, 3)))
