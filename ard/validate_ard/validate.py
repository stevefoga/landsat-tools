"""
validate.py

Validate Analysis Ready Data (ARD) tile bundles. The following steps are
performed:

1) check tar bundles using md5 sums
2) verify file naming conventions of tar file
3) extract contents of tar
4) verify number of files in tar
5) verify file naming conventions of each data file, qa, and metadata
6) verify xml with schema
7) verify projection (based on region)
8) verify extents
9) verify qa values are valid
10) verify fill values
11) verify data values within valid range
12) verify data type
13) verify saturate value
14) check if all fill (this is bad)

15) cleanup extracted files
16) print report

Author:         Steve Foga
Created:        02 August 2017
Modified:       02 August 2017
Version:        1.0
Python version: 3.5.2

Changelog
1.0     02 AUG 2017     Original development.
"""
import os
import sys
import glob
import re
import hashlib
import tarfile
import pandas as pd
from osgeo import gdal
from lxml import etree
import numpy as np
import lookup_dict
import time
import datetime


def map_md5_to_tar(tar_list, md5_list):
    """
    Match lists of strings to one another.

    :param tar_list: <list> List of .tar file name + extensions
    :param md5_list: <list> List of .md5 file name + extensions
    :return: <dict> Where {key=tar, value=md5}
    """
    def get_basename(files):
        """
        Get basename of files (first 40 characters.)

        :param files: <list> List of files.
        :return: <list> List of base file names.
        """
        fo = []
        for i in files:
            fo.append(os.path.basename(i)[:40])

        return fo

    # get base file names
    tf = get_basename(tar_list)
    mf = get_basename(md5_list)

    # find any differences
    diffs = set(tf).symmetric_difference(set(mf))

    if diffs:
        print("Mis-matched .tar and .md5 exist. Non-matched tiles: {0}".
              format(diffs))
        print("Please ensure all .tar and .md5 files are present!")
        sys.exit(1)

    # put all matches in a dictionary
    tar_md5 = {}
    for t in range(len(tar_list)):
        tar_md5[tar_list[t]] = md5_list[t]

    '''
    # VERY slow, but more precise way to determine file matches
    for t in tar_list:
        tm = [i for i, s in enumerate(md5_list) if os.path.splitext(t)[0] in s]

        if len(tm) == 1:
            tar_md5[t] = md5_list[tm[0]]

        elif len(tm) > 1:
            print("Multiple md5 files match tar file {0}: {1}".format(
                t, md5_list[tm]))

        else:
            print("No md5 found for tar file {0}".format(t))
    '''

    return tar_md5


def check_md5(fn_in, md5_in):
    """
    Make sure file hash and corresponding md5 hash match.

    :param fn_in: <str> Path to tar file.
    :param md5_in: <str> Path to MD5 file.
    :return: <bool> True (hashes match) or False (hashes do not match)
    """

    def read_file(fname, mode):
        """
        Open a file.

        :param fname: <str> Path to input file.
        :param mode: <str> Read/write mode.
        :return: <str> Contents of fname.
        """
        with open(fname, mode) as fn:
            data = fn.read()

        return data

    # generate hash for input file
    fn_hash = hashlib.md5(read_file(fn_in, 'rb')).hexdigest()

    # compare hash with md5
    md5_hash = read_file(md5_in, 'r').split(" ")[0]

    return fn_hash == md5_hash


def check_regex(regex, match_str):
    """
    Match string with regular expression.

    :param regex: <SRE_Pattern> Regex pattern created using re.compile()
    :param match_str: <str> String to be checked with regex pattern.
    :return: <bool> True if match, False if not match.
    """
    m = regex.match(match_str)
    if m:
        return True
    else:
        return False


def verify_basename(fn_in):
    """
    Validate base file name.

    :param fn_in: <str> File to be checked
    :return: <bool> True if match, False if no match
    """
    # regex string
    r_string = re.compile('^L[A,E,O,T][0][4-8]_'
                          '[CU,AK,HI]{2}_'
                          '[0][0-3][0-9][0][0-2][0-9]_'
                          '[1-2]\d{3}[0-1][0-9][0-3][0-9]_'
                          '[1-2]\d{3}[0-1][0-9][0-3][0-9]_'
                          'C\d{2}_'
                          'V\d{2}')

    # validate fn_in using r_string
    return check_regex(r_string, fn_in)


def extract_data(tar_in, dir_out=False):
    """
    Get contents of .tar, extract contents to directory.

    :param tar_in: <str> Path to .tar file.
    :param dir_out: <str> Output directory, else use tar_in directory.
    :return: <list> List of files in .tar file.
    """
    # open tar in read-only mode
    tar_open = tarfile.open(tar_in, 'r')

    # get file contents
    tar_files = tar_open.getnames()

    # extract files
    if not dir_out:
        dir_out = os.path.dirname(tar_in) + os.sep

    tar_open.extractall(path=dir_out)

    return tar_files


def verify_filenum(tar_in, fn_in):
    """
    Verify correct number of files in .tar archive.

    :param fn_in: <list> List of files in .tar generated by tar.getnames()
    :return: <bool> True if match, False if no match.
    """
    if 'LC08' in tar_in:
        if '_SR.tar' in tar_in:
            return len(fn_in) == 12
        elif '_TA.tar' in tar_in:
            return len(fn_in) == 16
        elif '_BT.tar' in tar_in:
            return len(fn_in) == 6
        elif '_QA.tar' in tar_in:
            return len(fn_in) == 5
        else:
            print("Type of file in verify_filenum could not be established.")
            return False

    elif 'LO08' in tar_in:
        if '_SR.tar' in tar_in:
            return len(fn_in) == 12
        elif '_TA.tar' in tar_in:
            return len(fn_in) == 16
        elif '_BT.tar' in tar_in:
            print("BT should not be present in OLI-only scenes.")
            return False
        elif '_QA.tar' in tar_in:
            return len(fn_in) == 5
        else:
            print("Type of file in verify_filenum could not be established.")
            return False

    elif any([i for i in ['LT04', 'LT05', 'LE07'] if i in tar_in]):
        if '_SR.tar' in tar_in:
            return len(fn_in) == 12
        elif '_TA.tar' in tar_in:
            return len(fn_in) == 14
        elif '_BT.tar' in tar_in:
            return len(fn_in) == 5
        elif '_QA.tar' in tar_in:
            return len(fn_in) == 6
        else:
            print("Type of file in verify_filenum could not be established.")
            return False

    else:
        print("Type of sensor in verify_filenum could not be established.")
        return False


def verify_fname(base, fn_in):
    """
    Verify all components of file name.

    :param base: <str> Base name, checked by verify_basename() function
    :param fn_in: <str> File name
    :return: <bool> True if match, False if no match.
    """
    if '.xml' in fn_in:
        r_string = re.compile(base + ".xml")

    elif any([i for i in ['SEA4', 'SEZ4', 'SOZ4', 'SOA4'] if i in fn_in]):
        r_string = re.compile(base + '_S[EA,EZ,OZ,OA]{2}4\.tif')

    elif base[0:4] == 'LC08' or base[0:4] == 'LO08':
        # L8-specific checks
        if 'SRB' in fn_in:
            r_string = re.compile(base + '_SRB[1-7]\.tif')

        elif 'BTB' in fn_in and base[0:4] != 'LO08':
            r_string = re.compile(base + '_BTB[10-11]{2}\.tif')

        elif 'TAB' in fn_in:
            r_string = re.compile(base + '_TAB[1-5,7]\.tif')

        elif 'QA' in fn_in:
            r_string = re.compile(base + "_[LINEAGE,RADSAT,PIXEL,SRAEROSOL]"
                                         "{0,}QA\.tif")

    else:
        # L4-5, L7-specific checks
        if 'SRB' in fn_in:
            r_string = re.compile(base + '_SRB[1-5,7]\.tif')

        elif 'BTB' in fn_in:
            r_string = re.compile(base + '_BTB6\.tif')

        elif 'TAB' in fn_in:
            r_string = re.compile(base + '_TAB[1-5,7]\.tif')

        elif 'QA' in fn_in:
            r_string = re.compile(base + '_[LINEAGE,RADSAT,PIXEL,SRCLOUD,'
                                         'SRATMOSOPACITY]{0,}QA\.tif')

    return check_regex(r_string, fn_in)


def get_regional_params(fn_in, csv_in):
    """
    Get tile extent and projection parameters for target tile.

    :param fn_in: <str> Tile ID string.
    :param csv_in: <str> Path to input csv file.
    :return: <dict> Dictionary of parameters.
    """

    def get_hv(fn):
        """
        Get h and v coordinates from tile ID.

        :param fn: <str> Tile ID name, without full path.
        :return: <tuple> h and v coordinates, as integers.
        """
        h = int(fn[8:11])
        v = int(fn[11:14])

        return h, v

    def get_extents(csv_file, h_crd, v_crd, region):
        """
        Get extents from CSV file.

        :param csv_file: <str> Path to CSV file.
        :param h_crd: <int> H coordinate.
        :param v_crd: <int> V coordinate.
        :param region: <str> Region identifier
        :return: <tuple> ulx,uly,lrx,lry coordinates, as int
        """
        # open csv
        df = pd.read_csv(csv_file)

        # sort csv by 'region'
        df_r = df.groupby('region').get_group(region)

        # get specific coordinates
        df_t = df_r[(df_r['h'] == h_crd) & (df_r['v'] == v_crd)]

        if len(df_t) != 1:
            print("Could not find extents for h{0}v{1} in region {2} using "
                  "CSV file {3}.".format(h_crd, v_crd, region, csv_file))
            return False

        return (int(df_t['ulx']), int(df_t['uly']), int(df_t['lrx']),
                int(df_t['lry']))

    param_dict = {}

    if 'CU' in fn_in:
        param_dict['region'] = 'CU'
        param_dict['proj'] = 'PROJCS["Albers",' \
                             'GEOGCS["WGS 84",' \
                             'DATUM["WGS_1984",' \
                             'SPHEROID["WGS 84",6378140,298.2569999999957,' \
                             'AUTHORITY["EPSG","7030"]],' \
                             'AUTHORITY["EPSG","6326"]],' \
                             'PRIMEM["Greenwich",0],' \
                             'UNIT["degree",0.0174532925199433],' \
                             'AUTHORITY["EPSG","4326"]],' \
                             'PROJECTION["Albers_Conic_Equal_Area"],' \
                             'PARAMETER["standard_parallel_1",29.5],' \
                             'PARAMETER["standard_parallel_2",45.5],' \
                             'PARAMETER["latitude_of_center",23],' \
                             'PARAMETER["longitude_of_center",-96],' \
                             'PARAMETER["false_easting",0],' \
                             'PARAMETER["false_northing",0],' \
                             'UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'

    elif 'AK' in fn_in:
        param_dict['region'] = 'AK'
        param_dict['proj'] = 'PROJCS["Albers",' \
                             'GEOGCS["WGS 84",' \
                             'DATUM["WGS_1984",' \
                             'SPHEROID["WGS 84",6378140,298.2569999999957,' \
                             'AUTHORITY["EPSG","7030"]],' \
                             'AUTHORITY["EPSG","6326"]],' \
                             'PRIMEM["Greenwich",0],' \
                             'UNIT["degree",0.0174532925199433],' \
                             'AUTHORITY["EPSG","4326"]],' \
                             'PROJECTION["Albers_Conic_Equal_Area"],' \
                             'PARAMETER["standard_parallel_1",55],' \
                             'PARAMETER["standard_parallel_2",65],' \
                             'PARAMETER["latitude_of_center",50],' \
                             'PARAMETER["longitude_of_center",-154],' \
                             'PARAMETER["false_easting",0],' \
                             'PARAMETER["false_northing",0],' \
                             'UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'

    elif 'HI' in fn_in:
        param_dict['region'] = 'HI'
        param_dict['proj'] = 'PROJCS["Albers",' \
                             'GEOGCS["WGS 84",' \
                             'DATUM["WGS_1984",' \
                             'SPHEROID["WGS 84",6378140,298.2569999999957,' \
                             'AUTHORITY["EPSG","7030"]],' \
                             'AUTHORITY["EPSG","6326"]],' \
                             'PRIMEM["Greenwich",0],' \
                             'UNIT["degree",0.0174532925199433],' \
                             'AUTHORITY["EPSG","4326"]],' \
                             'PROJECTION["Albers_Conic_Equal_Area"],' \
                             'PARAMETER["standard_parallel_1",8],' \
                             'PARAMETER["standard_parallel_2",18],' \
                             'PARAMETER["latitude_of_center",3],' \
                             'PARAMETER["longitude_of_center",-157],' \
                             'PARAMETER["false_easting",0],' \
                             'PARAMETER["false_northing",0],' \
                             'UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'

    else:
        print("Regional parameter in {0} is not correct.".format(fn_in))
        return False

    param_dict['h'], param_dict['v'] = get_hv(fn_in)
    param_dict['extents'] = {}
    param_dict['extents']['ulx'], param_dict['extents']['uly'], \
    param_dict['extents']['lrx'], \
    param_dict['extents']['lry'] = get_extents(csv_in, param_dict['h'],
                                               param_dict['v'],
                                               param_dict['region'])

    return param_dict


def verify_xml(xml_in, schema):
    """
    Verify XML against schema.

    :param xml_in: <str> Path to XML file to be checked.
    :param schema: <str> Path to XML schema.
    :return:
    """
    # read schema
    xmlschema = etree.XMLSchema(etree.parse(schema))

    # read XML
    xmlfile = etree.parse(xml_in)

    # do validation
    result = xmlschema.validate(xmlfile)

    return result


def verify_proj(ds, params):
    """
    Verify image projection is correct.

    :param ds: <osgeo.gdal.Dataset> Raster dataset object.
    :param fn_in: <str> Path to target raster.
    :param params: <dict> dictionary created by get_regional_parameters()
    :return: <bool> True if match, False if not match.
    """
    proj = ds.GetProjection()
    if params['proj'] == proj:
        return True
    else:
        return False


def verify_exts(ds, fn_in, params):
    """
    Verify image extents are correct.

    :param ds: <osgeo.gdal.Dataset> Raster dataset object.
    :param fn_in: <str> Path to target raster.
    :param params: <dict> dictionary created by get_regional_parameters()
    :return: <bool> True if match, False if not match.
    """
    # get grid dimensions
    extent = ds.GetGeoTransform()
    ulx = extent[0]
    uly = extent[3]
    x_dim = ds.RasterXSize
    y_dim = ds.RasterYSize

    # calculate lrx and lry
    lrx = ulx + (x_dim * extent[1])
    lry = uly + (y_dim * extent[5])

    # create output dict
    bool_dict = {'ulx': ulx == params['extents']['ulx'],
                 'uly': uly == params['extents']['uly'],
                 'lrx': lrx == params['extents']['lrx'],
                 'lry': lry == params['extents']['lry']}

    return bool_dict


def get_band_name(fn_in):
    """

    :param fn_in:
    :return:
    """
    return fn_in.split("_")[-1].split('.tif')[0]


def get_xml_entry(fn_in, xml_in):
    """

    :param fn_in: <str> File name (NOT path).
    :param xml_in: <str> Path to XML file.
    :return: <dict> Metadata for target band.
    """

    def get_tag(root, string, dict_type=None, dict_key=None):
        """
        Get index of target tag from root of XML tree.

        :param root: <lxml.etree._Element> Var read using
                                            etree.parse().getroot()
        :param string: <str> Search string for root children.
        :param dict_type: <str> Either 'tag' or 'attrib'.
        :param dict_key: <str> Key for use with 'attrib' dict_type.
        :return: <int> First matching tag index from root.
        """
        xta = []
        for child in root:
            if dict_type == 'tag':
                xta.append(child.tag)
            elif dict_type == 'attrib':
                xta.append(child.attrib)

        if dict_type == 'tag':
            tile_idx = [i for i, j in enumerate(xta) if string in j][0]
            return tile_idx

        elif dict_type == 'attrib' and dict_key:
            for i, dv in enumerate(xta):
                if xta[i][dict_key] == string:
                    return i

    def get_attrib(root, string):
        """
        Get specific attributes based on tag.

        :param root: <lxml.etree._Element> Var read using
                                            etree.parse().getroot()
        :param string: <str> Search string for root children.
        :return: <dict> Dictionary of metadata parameters
        """
        out = {}
        if type(string) is str:
            string = list(string)
        for child in root:
            if any([i for i in string if i in child.tag]):
                for k in child.attrib.keys():
                    out[k] = child.attrib[k]

        return out

    # get band name
    b_name = get_band_name(fn_in)

    # open xml
    xmlfile = etree.parse(xml_in)
    e = xmlfile.getroot()

    # locate where tile metadata is stored
    tidx = get_tag(e, 'tile_metadata', dict_type='tag')
    bidx = get_tag(e[tidx], 'bands', dict_type='tag')
    didx = get_tag(e[tidx][bidx], b_name, dict_type='attrib', dict_key='name')

    # get metadata
    band_mtd = e[tidx][bidx][didx].attrib

    # get other metadata attributes nested in band-level metadata
    more_mtd = get_attrib(e[tidx][bidx][didx], ['valid_range'])
    for m in more_mtd.keys():
        band_mtd[m] = more_mtd[m]

    return band_mtd


def check_qa_values(fn_in, values, ref_dict):
    """
    Check if array of values is in reference dictionary, by band and sensor.

    :param fn_in: <str> File (NOT path)
    :param values: <list> Unique values to be checked from input QA band.
    :param ref_dict: <dict>
    :return: <bool>
    """

    def get_sensor(sensor_str):
        """
        Translate sensor ID to string compatible with lookup_dict.

        :param sensor_str: <str> Two-number designation for Landsat sensor.
        :return: <str>
        """
        if any(i for i in ['04', '05', '07'] if i in sensor_str):
            return 'L47'
        elif '08' in sensor_str:
            return 'L8'
        else:
            return False

    def get_band_designation(band_str):
        """
        Translate band name to string compatible with lookup_dict.

        :param band_str: <str> Band name from file name.
        :return: <str>
        """
        if 'PIXEL' in band_str:
            return 'pixel_qa'
        elif 'RADSAT' in band_str:
            return 'radsat_qa'
        elif 'SRCLOUD' in band_str:
            return 'sr_cloud_qa'
        elif 'SRAEROSOL' in band_str:
            return 'sr_aerosol'
        else:
            return False

    # get sensor and band names
    sensor = get_sensor(fn_in[2:4])
    band = get_band_designation(get_band_name(fn_in))

    # query ref_dict for values
    if band == 'radsat_qa':
        ref_values = list(
            ref_dict[band].keys())  # radsat_qa is sensor-agnostic
    else:
        ref_values = list(ref_dict[band][sensor].keys())

    # check values against ref_values
    val_test = set(values).intersection(ref_values)

    # If same length of 'values' in 'val_test', the QA band is valid.
    if len(val_test) == len(values):
        return True
    else:
        return False


def check_img_params(ds, fn_in, mtd, is_qa=False, is_ang=False):
    """
    Check raster band against XML metadata.

    :param ds: <osgeo.gdal.Dataset> Raster dataset object.
    :param fn_in: <str> Path to input raster.
    :param metadata: <str> Path to XML file.
    :param is_qa: <bool> Set True if QA band, set False if image band.
    :param is_ang: <bool> Set True if angle band, set False if not.
    :return: <dict> Dict of bool values (True if match, false if no match)
    """
    # open raster band
    rb = ds.GetRasterBand(1)
    ab = rb.ReadAsArray()

    # check mtd against raster band values
    param_dict = {
        'NoData': rb.GetNoDataValue() == float(mtd['fill_value']),
        'HasValidPixels': ab.max() != float(mtd['fill_value']) or
                          ab.min() != float(mtd['fill_value']),
        'DataType': gdal.GetDataTypeName(rb.DataType).lower() ==
                    mtd['data_type'].lower()
    }

    if not is_ang:
        param_dict['Min'] = ab.min() >= float(mtd['min'])
        param_dict['Max'] = ab.max() <= float(mtd['max'])

    elif not is_qa and not is_ang:
        # qa has no saturation, so check if not qa
        param_dict['Saturate'] = ab.max() <= float(mtd['saturate_value'])

    elif is_qa:
        # ensure all qa values are valid
        # read image as array
        qa_arr = list(np.unique(ab))

        # read lookup dictionary
        qa_values = lookup_dict.qa_values

        # check values for matches
        param_dict['qa values valid'] = check_qa_values(
            os.path.basename(fn_in), qa_arr, qa_values)

    return param_dict


def main(dir_in, csv_in, xml_schema, dir_out, verbose=False):
    """
    Assumes input directory is not sorted by subfolder.

    :param dir_in: <str> Path to input tar file(s).
    :param csv_in: <str> Path to CSV of ARD tile extents.
    :param xml_schema: <str> Path to XML schema (.xsd) file.
    :param dir_out: <str> Path to where results will be written.
    :param verbose: <bool> If True, return all results, else, only return bad.
    :return: Text file written in dir_out location of test results.
    """
    t0 = time.time()

    # get files
    tars = sorted(glob.glob(dir_in + os.sep + "*.tar"))
    md5s = sorted(glob.glob(dir_in + os.sep + "*.md5"))

    # associate all tars with md5
    data_dict = map_md5_to_tar(tars, md5s)

    # create dictionary of results
    test_results = {}

    # run tests on each file in data_dict
    it = 0
    for dd in data_dict.keys():
        # archive tests
        bn = os.path.basename(dd)
        base_fn = bn[:40]
        test_results[bn] = {}
        test_results[bn]['md5 match'] = check_md5(dd, data_dict[dd])
        test_results[bn]['basename correct'] = verify_basename(bn)

        # get geospatial parameters
        geo = get_regional_params(bn, csv_in)

        # per-file tests
        ext_files = extract_data(dd)
        test_results[bn]['number of files correct'] = verify_filenum(dd,
                                                                     ext_files)

        # verify xml against schema
        xml_file = [i for i in ext_files if '.xml' in i]
        xml_path = dir_in + os.sep + xml_file[0]
        test_results[bn][xml_file[0]] = {}
        test_results[bn][xml_file[0]]['xml schema valid'] = verify_xml(
            xml_path, xml_schema)

        for ff in ext_files:
            # filename test
            test_results[bn][ff] = {}
            test_results[bn][ff]['filename correct'] = verify_fname(base_fn,
                                                                    ff)

            # build full filename
            fn = dir_in + os.sep + ff

            # geospatial & image properties parameter tests
            if '.tif' in ff:
                ds = gdal.Open(fn)
                test_results[bn][ff]['projection correct'] = verify_proj(ds,
                                                                         geo)
                test_results[bn][ff]['extents correct'] = verify_exts(ds, fn,
                                                                      geo)

                # parse XML metadata for band-specific information
                xml_dict = get_xml_entry(ff, xml_path)

                # verify xml parameters in band data
                if xml_dict['product'] == 'angle_bands':
                    test_results[bn][ff]['angle characteristics'] = \
                        check_img_params(ds, fn, xml_dict, is_ang=True)

                elif xml_dict['category'] == 'image' \
                        and xml_dict['name'] != 'SRATMOSOPACITYQA':
                    test_results[bn][ff]['image characteristics'] = \
                        check_img_params(ds, fn, xml_dict)

                elif xml_dict['category'] == 'qa' \
                        and xml_dict['name'] == 'SRATMOSOPACITYQA':
                    test_results[bn][ff]['qa characteristics'] = \
                        check_img_params(ds, fn, xml_dict, is_qa=True)

            ds = None

        # clean up only extracted files
        for file in ext_files:
            os.remove(dir_in + os.sep + file)

        it += 1
        print("Archive {0} of {1} checked.".format(it, len(data_dict.keys())))

    # if verbose is disabled, return only the invalid products
    if not verbose:
        # nasty nested for loops; is there a recursive solution to this that
        #   maintains the structure of the original dictionary?
        for basename in list(test_results):
            for band in list(test_results[basename]):
                if type(test_results[basename][band]) is bool:
                    if test_results[basename][band]:
                        test_results[basename].pop(band)
                else:
                    for check in list(test_results[basename][band]):
                        if test_results[basename][band][check]:
                            test_results[basename][band].pop(check)

    # generate timestamp
    dt = str(int(float(str(datetime.datetime.now()).replace('-', '').
                       replace(':', '').replace(' ', ''))))

    if verbose:
        fn_out = dir_out + os.sep + 'validate_tiles_' + dt + '_verbose.txt'
    else:
        fn_out = dir_out + os.sep + 'validate_tiles_' + dt + '.txt'

    # write results to text file
    # another nasty nest of for loops to handle nested dict; csv.DictWriter()
    #   is an option, but writes columns, which test_results lacks.
    with open(fn_out, 'w') as f:
        for k in list(test_results):
            f.write('{0}\n'.format([k]))
            for ik in list(test_results[k]):
                f.write('\t\t{0}\n'.format(ik))
                if type(test_results[k][ik]) is bool:
                    #if verbose or not test_results[k][ik]:
                    f.write('\t\t\t\t{0}: {1}\n'.format(
                        ik, test_results[k][ik]))
                else:
                    for iik in list(test_results[k][ik]):
                        #if verbose or not test_results[k][ik][iik]:
                        f.write('\t\t\t\t{0}: {1}\n'.format(
                            iik, test_results[k][ik][iik]))

    print("Results written to {0}".format(fn_out))

    t1 = time.time()
    m, s = divmod(t1 - t0, 60)
    h, m = divmod(m, 60)
    print("Total runtime: {0}h, {1}m, {2}s.".format(h, round(m, 3),
                                                    round(s, 3)))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    req_named = parser.add_argument_group('Required named arguments')

    req_named.add_argument('-d', action='store', dest='dir_in', type=str,
                           help='Input directory', required=True)

    req_named.add_argument('-c', action='store', dest='csv_in', type=str,
                           help='Input CSV with ARD tile extents',
                           required=True)

    req_named.add_argument('-x', action='store', dest='xml_schema',
                           type=str, help='XML schema', required=True)

    req_named.add_argument('-o', action='store', dest='dir_out',
                           help='Output directory', required=True)

    parser.add_argument('--verbose', action='store_true', dest='verbose',
                        help='Verbose', required=False)

    arguments = parser.parse_args()

    main(**vars(arguments))
