"""
create_scenelist_from_metdata.py

Purpose:  For all CSV files in a directory, open them, grab the first column
          of data, combine them, and output into a single text file.
          
          Useful if multiple metadata files created by EarthExplorer, and need
          a single text file to submit to ESPA.

          
Inputs:   Directory containing target file(s).
Output:   Single text file of one column of data.

Tested versions: Python 3.5.x

Author:   Steve Foga
Created:  31 October 2016
Modified: 17 March 2017

Changelog:
  31 Oct 2016: Original development.
  17 Mar 2017: PEP8 compliance, added argparse, added filetype option, added
                column index option, added row skipping, added delimiter
                option, added dir_out specification, cleanup
"""


def scene_from_meta(dir_in, ext='csv', dir_out=False, column=0, rowskip=None,
                    delim=','):
    import os
    import sys
    import csv
    import glob

    # find all text files
    fn_in = glob.glob(dir_in + os.sep + "*" + ext)

    if not fn_in:
        print("No input {0} file(s) found!".format(ext))
        sys.exit(1)

    # allocate variable for scene ids
    sid = []

    # read sceneID column from each text file
    it = 0
    for i in fn_in:
        # open file
        with open(i, 'r') as f:
            # read file with csv.reader()
            reader = list(csv.reader(f, delimiter=delim))

            # grab specified column from each row
            for x in range(len(reader)):
                if x != rowskip:
                    sid.append([reader[x][column]])

            it += 1
            print("File {0} of {1} read.".format(it, len(fn_in)))

    # flatten sid to single list
    sid = [item for sublist in sid for item in sublist]

    # create output name
    if dir_out:
        fn_out = dir_out + os.sep + "_combined.txt"

    else:
        dir_name = dir_in.split(os.sep)[-1]
        fn_out = dir_in + os.sep + dir_name + "_combined.txt"

    # write out new text file
    print("Writing data to text file...")
    with open(fn_out, 'w') as fo:
        for line in sid:
                fo.write(line + '\n')

    print("Data written to {0}.".format(fn_out))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Combine contents a single column in multiple CSV files '
                    'info a single text file.',
        epilog='Example usage: '
               'python create_scenelist_from_metadata.py -i '
               '/path/to/your/dir/ -r 0 -c 1 -delim ","')

    req_named = parser.add_argument_group('Required named arguments')

    req_named.add_argument('-i', action='store', dest='dir_in', type=str,
                           help='Directory containing CSV files',
                           required=True)

    parser.add_argument('-d', action='store', dest='dir_out', type=str,
                        default=False,
                        help='Output directory (default=input dir.)',
                        required=False)

    parser.add_argument('-e', action='store', dest='ext', type=str,
                        default='csv', help='File extension (default=csv)',
                        required=False)

    parser.add_argument('-c', action='store', dest='column', type=int,
                        default=0, help='Target column index (default=0)',
                        required=False)

    parser.add_argument('-r', action='store', dest='rowskip', type=int,
                        default=None, help='Row index to skip (default=None)',
                        required=False)

    parser.add_argument('-delim', action='store', dest='delim', type=str,
                        default=',', help='Delimiter (default=",")',
                        required=False)

    arguments = parser.parse_args()

    scene_from_meta(**vars(arguments))
