"""qa_metadata.py"""
import os
import logging


class MetadataQA:
    @staticmethod
    def check_text_files(test, mast, ext):
        """Check master and test text-based files (headers, XML, etc.)
        line-by-line for differences.
        Sort all the lines to attempt to capture new entries.

        Args:
            test <str>: path to test text file
            mast <str>: path to master text file
            ext <str>: file extension (should be .txt, .xml or .gtf
        """
        from file_io import Cleanup

        logging.info("Checking {0} files...".format(ext))

        test, mast = Cleanup.remove_nonmatching_files(test, mast)

        # Do some checks to make sure files are worth testing
        if mast is None or test is None:
            logging.warning("No {0} files to check in test and/or mast "
                            "directories.".format(ext))
            return

        if len(mast) != len(test):
            logging.error("{0} file lengths differ. Master: {1} | Test:"
                " {2}".format(ext, len(mast), len(test)))
            return

        for i, j in zip(test, mast):
            topen = open(i)
            mopen = open(j)

            # Read text line-by-line from file
            file_topen = topen.readlines()
            file_mopen = mopen.readlines()

            # Close files
            topen.close()
            mopen.close()

            # Check file names for name differences.
            # Print non-matching names in details.
            # get file names
            i_fn = i.split(os.sep)[-1]
            j_fn = j.split(os.sep)[-1]
            if i_fn != j_fn:
                logging.error("{0} file names differ. Master: {1} | Test: {2}".
                              format(ext, i, j))
                return
            else:
                logging.info("{0} file names equivalent. Master: {1} | Test: "
                             "{2}".format(ext, i, j))

            # Check open files line-by-line (sorted) for changes.
            # Print non-matching lines in details.
            txt_diffs = set(file_topen).difference(set(file_mopen))
            if len(txt_diffs) > 0:
                for k in txt_diffs:
                    logging.error("{0} changes: {1}".format(ext, k))

            else:
                logging.info("No differences between {0} and {1}.".
                             format(i, j))

    @staticmethod
    def check_jpeg_files(test, mast, dir_out):
        """Check JPEG files (i.e., Gverify or preview images) for diffs in file
        size or file contents. Plot difference image if applicable.

        Args:
            test <str>: path to test jpeg file
            mast <str>: path to master jpeg file
            dir_out <str>: output directory for difference image
        """
        from qa_images import ArrayImage
        from file_io import ImWrite, Cleanup

        test, mast = Cleanup.remove_nonmatching_files(test, mast)
        logging.info("Checking JPEG preview/gverify files...")

        if mast is None or test is None:
            logging.error("No JPEG files to check in test and/or mast "
                          "directories.")

        else:
            if len(test) > 0 and len(mast) > 0:
                for i, j in zip(test, mast):

                    # Compare file sizes
                    if os.path.getsize(i) != os.path.getsize(j):
                        logging.warning("JPEG file sizes do not match for "
                                        "Master {0} and Test {1}...\n".
                                        format(j, i))
                        logging.warning("{0} size: {1}".format(
                            i, os.path.getsize(i)))
                        logging.warning("{0} size: {1}".format(
                            j, os.path.getsize(j)))

                    else:
                        logging.info("JPEG files {0} and {1} are the same "
                                     "size".format(j, i))

                    # diff images
                    result = ArrayImage.check_images(test, mast)

                    if result:
                        ImWrite.plot_image_diff(result, i.split(os.sep)[-1],
                                                "diff", dir_out)
