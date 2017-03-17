"""
extract_band.py

Purpose:    Extract one or more files from a .tar.gz archive using a wildcard.

Inputs: .tar.gz archive file; search string
Output: extracted file(s)

Example usage:
    python extract_band.py -i /path/to/your/archive.tar.gz -s '*qa*'
                            -d /path/to/your/output_directory

Tested version: Python 3.5.x

Author:   Steve Foga
Created:  19 September 2016
Modified: 17 March 2017

Changelog:
  19 Sep 2016: Original development
  17 Mar 2017: PEP8 compliance, added wildcard, added argparse, cleanup
"""


def extract(input_gz, file_str, dir_out=False):
    """
    Extract file(s) from .tar.gz archive using wildcard search string.

    :param input_gz: <str> path to .tar.gz archive.
    :param file_str: <str> search string, with wildcards as necessary
    :param dir_out: <str> path to output directory (default=use input_gz dir.)
    :return:
    """
    import os
    import sys
    import tarfile
    import fnmatch

    # function to extract files
    def extract_file(fn_in, fn_out):

        print("Extracting {0} to {1}...".format(fn_in, fn_out))
        try:
            tar.extract(fn_in, fn_out)

        except KeyError:
            print("Could not find specified file {0}".format(fn_in))
            sys.exit(1)

        print("Complete.\n")

    # get output directory
    if not dir_out:  # defer to same dir as tar_in
        dir_out = os.path.dirname(input_gz)

    # Extract target file(s) from gz archive
    print("Opening archive...")
    tar = tarfile.open(input_gz)

    # get all file names from archive
    file_names = tar.getnames()

    # find only desired files by string
    tarout = fnmatch.filter(file_names, file_str)

    if tarout:
        for i in tarout:
            extract_file(i, dir_out)
    else:
        print("No files found in {0} using search string {1}"
              .format(input_gz, file_str))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract one or more files from a .tar.gz archive. '
                    'Setup to support geotagged images, as a call for .img '
                    'will retrieve both the .img and corresponding .hdr file.',
        epilog='Example usage: '
               'python extract_band.py -i /path/to/your/archive.tar.gz -s '
               '"*qa*"')

    req_named = parser.add_argument_group('Required named arguments')

    req_named.add_argument('-i', action='store', dest='input_gz', type=str,
                           help='Input .tar.gz archive', required=True)

    req_named.add_argument('-s', action='store', dest='file_str', type=str,
                           help='Search string, with wildcards as necessary',
                           required=True)

    parser.add_argument('-d', action='store', dest='dir_out', type=str,
                        help='Output directory (default=input dir.)',
                        required=False)

    arguments = parser.parse_args()

    extract(**vars(arguments))
