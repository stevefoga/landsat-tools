"""
fild_pathrows_in_tile.py

Purpose: find all Landsat acquisitions within each Landsat Analysis Ready Data
 (ARD) tile. Check precisely by building boundary extents of each acq., and
 intersecting it with the tile extents, using OGR.

 Return CSV files with per-tile scene counts, scene counts per path/row per
 tile, and scene counts per sensor per tile. Also return text file of product
 IDs for each tile.

Author:         Steve Foga
Created:        14 July 2017
Modified:       14 July 2017
Version:        1.0
Python version: 2.7.8, 3.5.2

Changelog
    1.0     14 JUL 2017     Original development.

"""
import os
import json
from osgeo import ogr, osr
import pandas as pd
import time

t00 = time.time()


def rm_leading_zero(string):
    """
    Remove zeros in numeric portions of hXXvYY strings.

    :param string: <str> String to be parsed.
    :return: <list> String with leading zeros removed, inside a list.
    """
    return [int(i) for i in string.split('h')[-1].split('v')]


def build_hv_string(c_pair):
    """
    Build list of integers into hXXvYY coordinate pair strings.

    :param c_pair: <list> List of inters to be converted into string.
    :return: <str> Integer list re-formatted into string.
    """
    return 'h{0}v{1}'.format(c_pair[0], c_pair[1])


def open_shp(shp_in):
    """
    Open ESRI Shapefile as OSR Layer object.

    :param shp_in: <str> Path to shapefile.
    :return: <osgeo.osr.Layer> OSR Layer object.
    """
    driver = ogr.GetDriverByName("ESRI Shapefile")

    return driver.Open(shp_in, 0)


def build_sql(ds_name, column, column_cond):
    """
    Create SQL statement.

    :param ds_name: <str> Name of dataset to be accessed.
    :param column: <str> Name of column within dataset.
    :param column_cond: <str> Name of item within column.
    :return: <str> SQL string.
    """
    return "SELECT * FROM {0} WHERE {1}='{2}'".format(ds_name,
                                                      column,
                                                      column_cond)


def get_bounds(input_layer):
    """
    Get boundary coordinate pairs of feature layer.

    :param input_layer: <osgeo.ogr.Feature> Input layer.
    :return: <tuple> Tuple of values (minX, maxX, minY, maxY)
    """
    return input_layer.GetGeometryRef().GetEnvelope()


def bounds2dict(input_bounds):
    """
    Organize bounding coordinates into a dictionary.

    :param input_bounds: <tuple> Tuple of values (minX, maxX, minY, maxY)
    :return: <dict> Dictionary of coordinates.
    """
    out = {'minX': input_bounds[0],
           'maxX': input_bounds[1],
           'minY': input_bounds[2],
           'maxY': input_bounds[3]}

    return out


def proj2geo(input_ref, input_layer):
    """
    Warp input layer to geographic (a.k.a. EPSG 4326).

    :param input_ref: <osgeo.osr.SpatialReference> Spatial reference object.
    :param input_layer: <str> Wkt string of polygon coordinates.
    :return: <dict> Dictionary of coordinate values.
    """
    # create coordinate transformation
    output_ref = osr.SpatialReference()
    output_ref.ImportFromProj4('+proj=longlat +ellps=WGS84 '
                               '+datum=WGS84 +no_defs')

    c_trans = osr.CoordinateTransformation(input_ref, output_ref)

    # get layer boundaries
    bound_coords = get_bounds(input_layer)

    # make target points (one for UL, one for LR)
    def make_pts(xpt, ypt, coord_trans):
        """
        Get points, transform to output ref system.

        :param xpt: <int or float> X value to be warped.
        :param ypt: <int or float> Y value to be warped.
        :param coord_trans: <osgeo.osr.CoordinateTransformation>
        :return: <osgeo.ogr.Geometry> Geometry with points.
        """
        # add point
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(xpt, ypt)

        # do transformation
        point.Transform(coord_trans)

        # get transformed coordinate pair
        x, y, c = point.GetPoints()[0]

        return x, y

    minX, maxY = make_pts(bound_coords[0], bound_coords[3], c_trans)  # UL
    maxX, minY = make_pts(bound_coords[1], bound_coords[2], c_trans)  # LR

    # get bounds of WGS84 points
    return bounds2dict((minX, maxX, minY, maxY))


def build_polygon(poly_coords):
    wkt1 = "POLYGON (({0} {1}, {2} {3}, {4} {5}, {6} {7}, {0} {1}))". \
        format(poly_coords['minX'],
               poly_coords['maxY'],

               poly_coords['minX'],
               poly_coords['minY'],

               poly_coords['maxX'],
               poly_coords['minY'],

               poly_coords['maxX'],
               poly_coords['maxY'])

    return wkt1


def get_polygon(dataset, tile_id):
    """
    Open shapefile, extract specific polygon using SQL, return dataset AND
    polygon (polygon will not work outside of function without dataset intact.)

    :param dataset: <str> Path to ESRI shapefile.
    :param tile_id: <str> H/V coordinate pair.
    :return: <str, osgeo.ogr.Layer> Extracted Proj4 info, Wkt polygon info.
    """

    def get_pr(feat):
        """
        Get path and row from each polygon feature.

        :param feat: <osgeo.ogr.Feature> Feature layer containing path and row.
        :return: <list> Path and row values from feature.
        """
        # read feature properties as JSON
        j_feat = json.loads(feat.ExportToJson())
        pp = j_feat['properties']['PATH']
        rr = j_feat['properties']['ROW']

        return [pp, rr]

    def get_sref(dataset):
        """
        Get spatial reference from feature.

        :param dataset: <osgeo.ogr.Feature> Input feature.
        :return: <osgeo.ogr.SpatialReference> Spatial reference object.
        """
        return dataset.GetSpatialRef()

    # open shapefile
    ds = open_shp(dataset)

    # re-format tile id
    hv = build_hv_string(rm_leading_zero(tile_id))

    # build SQL argument
    poly = ds.ExecuteSQL(build_sql(ds.GetLayer().GetName(), 'h_v', hv))

    # Call each feature from polygon (this only access the individual feature)
    pp = []
    rr = []
    for feature in poly:
        # get path/row
        p_r = get_pr(feature)
        pp.append(p_r[0])
        rr.append(p_r[1])

        # get geom info
        feature.GetGeometryRef()

    # get spatial reference
    s_ref = get_sref(poly)

    # make output dataframe for path/row info
    pr_out = pd.DataFrame({'path': pd.Series(pp),
                           'row': pd.Series(rr)})

    if feature:
        return s_ref, pr_out, feature
    else:
        return False


def check_bounding_box(dframe, x_point, y_point):
    """
    Return rows that intersect with target bounding boxes.

    :param dframe: <pd.DataFrame> Input dataframe.
    :param x_point: <int or float> X coordinate.
    :param y_point: <int or float> Y coordinate.
    :return: <pd.DataFrame>
    """
    df_bound = dframe[((x_point >= dframe['minX']) &
                       (x_point <= dframe['maxX'])) &
                      ((y_point >= dframe['minY']) &
                       (y_point <= dframe['maxY']))
                      ]

    return df_bound


def build_metadata_polygon(dframe):
    """
    Build well-known text (wkt) from corner points.

    :param dframe: <pd.DataFrame> Input dataframe.
    :return: <str> Well-known text string.
    """
    wkt1 = "POLYGON (({0} {1}, {2} {3}, {4} {5}, {6} {7}, {0} {1}))". \
        format(float(dframe['upperLeftCornerLongitude']),
               float(dframe['upperLeftCornerLatitude']),

               float(dframe['lowerLeftCornerLongitude']),
               float(dframe['lowerLeftCornerLatitude']),

               float(dframe['lowerRightCornerLongitude']),
               float(dframe['lowerRightCornerLatitude']),

               float(dframe['upperRightCornerLongitude']),
               float(dframe['upperRightCornerLatitude']))

    return wkt1


def make_geom(wkt):
    """
    Convert well-known text string to geometry.

    :param wkt: <str> Well-known text (wkt) geometry.
    :return: <osgeo.ogr.Geometry>
    """
    return ogr.CreateGeometryFromWkt(wkt)


def main(tile_list, shp_in, sensor_datafile, dir_out):
    """
    Filter metadata by categories defined in config file, find unique path/
    rows, return CSV files with per-tile scene counts, scene counts per path/
    row per tile, and scene counts per sensor per tile. Also return text file
    of product IDs for each tile.

    :param tile_list: <list> List of tiles in 'hXvY' or 'hXXvYY' format
    :param shp_in: <str> Path to tile shapefile
    :param sensor_datafile: <str> Path to JSON file with sensor parameters
    :param dir_out: <str> Path to output directory for CSV files
    :return:
    """
    print("Tile list: {0}".format(tile_list))
    # open target polygon(s), get coordinates in WGS84 geographic space
    polygon = {}
    for tile in tile_list:
        polygon[tile] = {}
        s_ref, path_rows, poly = get_polygon(shp_in, tile)
        polygon[tile]['coords'] = proj2geo(s_ref, poly)
        polygon[tile]['pr'] = path_rows

    # read sensor data file
    with open(sensor_datafile, 'r') as myfile:
        sensor_data = json.load(myfile)

    # read metadata file for each sensor, do calculations for each tile
    pr_out = pd.DataFrame()
    for s in sensor_data.keys():
        # load metadata
        print("Reading {0} metadata...".format(s))
        # if a list of cols was provided in config file, use those to reduce
        # memory and proc time for dataframes, else read everything
        if sensor_data[s]['use_columns']:
            df = pd.read_csv(sensor_data[s]['metadata'],
                             usecols=[str(c) for c in
                                      sensor_data[s]['use_columns']])
        else:
            df = pd.read_csv(sensor_data[s]['metadata'])

        # initially filter data for known desired parameters (Tiers, etc.)
        df_out = df[df['COLLECTION_CATEGORY'].isin(sensor_data[s]['tiers']) &
                    df['COLLECTION_NUMBER'].isin(
                        sensor_data[s]['collection']) &
                    df['sensor'].isin(sensor_data[s]['sensor_id'])]

        # filter by path/row (if specified)
        print("Filtering metadata...")
        if sensor_data[s]['path_minmax']:
            path_mm = [int(i) for i in sensor_data[s]['path_minmax']]
            df_out = df_out[(df_out['path'] >= path_mm[0]) &
                            (df_out['path'] <= path_mm[1])]

        if sensor_data[s]['row_minmax']:
            row_mm = [int(i) for i in sensor_data[s]['row_minmax']]
            df_out = df_out[(df_out['row'] >= row_mm[0]) &
                            (df_out['row'] <= row_mm[1])]

        # filter by date (if specified)
        date_start = sensor_data[s]['start']
        date_end = sensor_data[s]['end']

        if date_start and date_end:
            df_out = df_out[(df_out['acquisitionDate'] <= date_end) &
                            (df_out['acquisitionDate'] >= date_start)]

        elif date_start:
            df_out = df_out[(df_out['acquisitionDate'] >= date_start)]

        elif date_end:
            df_out = df_out[(df_out['acquisitionDate'] <= date_end)]

        # remove no aux dates (if applicable)
        if sensor_data[s]['no_aux']:
            df_out = df_out[~df_out[
                'acquisitionDate'].isin(sensor_data[s]['no_aux'])]

        # filter by sun elevation
        df_out = df_out[df_out['sunElevation'] > 14.0]

        t0 = time.time()

        # for each tile, filter data by bounding extents
        for pps in polygon:
            print("Building reference tile(s)...")

            # add empty dataframe to be filled later
            polygon[pps]['df'] = pd.DataFrame()

            # make tile polygon
            polygon[pps]['poly'] = make_geom(build_polygon(
                polygon[pps]['coords']))

        # loop through each metadata entry, build tile, compare against
        for index, row in df_out.iterrows():
            o_poly = make_geom(build_metadata_polygon(row))

            for pt in polygon:
                # check to see if two tiles intersect
                p_sect = polygon[pt]['poly'].Intersect(o_poly)

                # if the intersection yields valid geometry, add to dataframe
                if p_sect:
                    polygon[pt]['df'] = polygon[pt]['df'].append(row)

        # find unique path/row combos, get counts of each category
        unique_pr = pd.DataFrame()
        product_ids = {}
        for idf in polygon:
            # get all unique path/rows, append to single list
            product_ids[idf] = polygon[idf]['df']['LANDSAT_PRODUCT_ID']. \
                tolist()

            # write results to single DataFrame, aggregate by sensor and p/r
            df_final = polygon[idf]['df'].groupby(
                ['path', 'row', 'sensor']).size(). \
                reset_index().rename(columns={0: 'count'})
            df_final['tile'] = idf

            unique_pr = unique_pr.append(df_final)

        # path and row come out as floats, convert to int
        unique_pr[['path', 'row']] = unique_pr[['path', 'row']].astype(int)

        # TODO: find which path/rows are not nominal

        # append results to single dataframe
        pr_out = pr_out.append(unique_pr)

        t1 = time.time()
        print("Elapsed time: {0} seconds".format(t1 - t0))

    # make multiple tables to output to CSV
    # 1) remove sensor component
    per_tile_pr = pr_out.groupby(['tile', 'path', 'row'])['count'].sum(). \
        reset_index()
    per_tile_pr.to_csv(dir_out + os.sep + 'per_tile-per_pr.csv', index=False)

    # 2) get single count for each tile
    per_tile = pr_out.groupby(['tile'])['count'].sum().reset_index()
    per_tile.to_csv(dir_out + os.sep + 'per_tile.csv', index=False)

    # 3) break out counts by sensor for each tile
    per_tile_sen = pr_out.groupby(['tile', 'sensor'])['count'].sum(). \
        reset_index()
    per_tile_sen.to_csv(dir_out + os.sep + 'per_tile-per_sensor.csv',
                        index=False)

    # write product id data frames to unique text files
    for pid in product_ids:
        txt_out = dir_out + os.sep + pid + '.txt'
        with open(txt_out, 'w') as ft:
            ft.writelines("%s\n" % item for item in product_ids[pid])

    t11 = time.time()
    print("Total elapsed time: {0} seconds".format(t11 - t00))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    req_named = parser.add_argument_group('Required named arguments')

    req_named.add_argument('-t', action='store', dest='tile_list', type=str,
                           nargs='+', help='List of tile coordinates',
                           required=True)

    req_named.add_argument('-s', action='store', dest='shp_in', type=str,
                           help='Input shapefile', required=True)

    req_named.add_argument('-d', action='store', dest='sensor_datafile',
                           type=str, help='Path to JSON config file',
                           required=True)

    req_named.add_argument('-o', action='store', dest='dir_out',
                           help='Output directory', required=True)

    arguments = parser.parse_args()

    main(**vars(arguments))
