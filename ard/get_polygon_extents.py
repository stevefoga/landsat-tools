"""
get_polygon_extents.py

Purpose: Get bounding box of polygon(s) in a shapefile, return in CSV with
        other attributes.
        If grid_res is specified, the grid will be snapped to the nearest
        interval of grid_res. Offsets can also be manually specified in the X
        and Y directions.

Author:         Steve Foga
Created:        14 July 2017
Python version: 3.5.2
"""
import sys
import os
import csv

try:
    from osgeo import ogr
except ImportError:
    import ogr


def do_mins(coord, grid_res):
    """
    Determine minimum coordinate divisible by grid resolution.

    :param coord: <int or float> Coordinate value.
    :param grid_res: <int> Grid resolution for snapping.
    :return: <int or float>
    """
    oix = coord % grid_res
    xmin_final = coord - (grid_res - oix)

    if (xmin_final % grid_res) != 0:
        xmin_final = coord - (grid_res + oix)

    return xmin_final


def do_maxs(coord, grid_res):
    """
    Determine maximum coordinate divisible by grid resolution.

    :param coord: <int or float> Coordinate value.
    :param grid_res: <int> Grid resolution for snapping.
    :return: <int or float>
    """
    oix = coord % grid_res
    xmax_final = coord + (grid_res + oix)

    if (xmax_final % grid_res) != 0:
        xmax_final = coord + (grid_res - oix)

    return xmax_final


def isint(x):
    """
    Check if value inside string is a float or integer.

    :param x: <str> String containing only numeric values.
    :return: <bool>
    """
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b


def main(shp_in, dir_out, offset_x=0, offset_y=0, data_cols=None,
         grid_res=None):
    """
    Open shapefile, get contents, determine extents, write results to CSV.

    :param shp_in: <str> Path to input ESRI Shapefile.
    :param dir_out: <str> Path to write out CSV file.
    :param offset_x: <int or flt> X units to offset grid.
    :param offset_y: <int or flt> Y units to offset grid.
    :param data_cols: <list> List of columns to go from shp to CSV file. Column
                             values expected to be integer!
    :param grid_res: <int> Specify grid resolution for snapping.
    :return:
    """
    # get 'ESRI shapefile' driver
    driver = ogr.GetDriverByName('ESRI Shapefile')
    s_in = driver.Open(shp_in, 0)
    if not s_in:
        sys.exit("Could not open shapefile {0}".format(shp_in))

    # get data layer
    layer = s_in.GetLayer()

    # loop through each feature in the layer, determine bbox & offset interval
    cols_out = ['ulx', 'uly', 'lrx', 'lry']
    if data_cols:
        for col in reversed(data_cols):
            cols_out = [col] + cols_out

    data_out = []
    for feature in layer:
        d_out = []

        # grab columns for each feature
        if data_cols:
            for cc in data_cols:
                # get feature column's value
                field = feature.GetFieldAsString(cc)

                # write value out with same data type as input
                if field.isdigit():
                    if isint(field):
                        d_out.append(int(field))
                    else:
                        d_out.append(float(field))
                else:
                    d_out.append(field)

        # grab bounding box for each feature
        geoms = feature.GetGeometryRef().GetEnvelope()

        # shift extents according to grid offsets
        xmin = round(geoms[0] - offset_x)
        xmax = round(geoms[1] + offset_x)
        ymin = round(geoms[2] - offset_y)
        ymax = round(geoms[3] + offset_y)

        # calculate closest x_origin,y_origin to grid_res
        if grid_res:
            xmin = do_mins(xmin, grid_res)
            ymin = do_mins(ymin, grid_res)
            xmax = do_maxs(xmax, grid_res)
            ymax = do_maxs(ymax, grid_res)

        # Combine output into list
        d_out.extend([xmin, ymax, xmax, ymin])
        data_out.append([d_out])

    # write list to CSV
    fn = os.path.splitext(os.path.basename(shp_in))[0]
    fn_out = dir_out + os.sep + fn + "_extent_buffer_offset.csv"

    with open(fn_out, 'w', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(cols_out)  # write header
        for row in data_out:
            writer.writerows(row)

    print("Data written to {0}".format(fn_out))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    req_named = parser.add_argument_group('Required named arguments')

    req_named.add_argument('-s', action='store', dest='shp_in', type=str,
                           help='Input shapefile', required=True)

    req_named.add_argument('-o', action='store', dest='dir_out',
                           help='Output directory', required=True)

    parser.add_argument('-x', action='store', dest='offset_x',
                        help='X offset', required=False, default=0)

    parser.add_argument('-y', action='store', dest='offset_y',
                        help='Y offset', required=False, default=0)

    parser.add_argument('-dc', action='store', dest='data_cols',
                        type=str, nargs='+',
                        help='Data column(s) to extract from shp',
                        required=False, default=None)

    parser.add_argument('-gr', action='store', dest='grid_res',
                        type=int,
                        help='Grid resolution (for snapping extents)',
                        required=False, default=None)

    arguments = parser.parse_args()

    main(**vars(arguments))
