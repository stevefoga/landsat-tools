"""image_io.py

Purpose: contains functions to read image data and extract metadata.
"""
import numpy as np
import logging

try:
    from osgeo import gdal
except ImportError:
    import gdal


class RasterIO:
    @staticmethod
    def open_raster(i):
        """Open raster as GDAL object
        Args:
            i <str>: path to raster file
        """
        ds_raster = gdal.Open(i, gdal.GA_ReadOnly)
        return ds_raster

    @staticmethod
    def get_sds(file):
        """Get sub/science data sets from raster

        Args:
            file <osgeo.gdal.Dataset>: open raster containing SDS
        """
        sds = file.GetSubDatasets()
        return sds

    @staticmethod
    def open_hdf(i):
        """Get sub/science data sets from hdf

        Args:
            i <osgeo.gdal.Dataset>: open HDF containing SDS
        """
        ds_raster = RasterIO.get_sds(i)
        return ds_raster

    @staticmethod
    def read_band_as_array(rast, n_bands=1):
        """Read gdal object as an array. Mask out nodata.

        Args:
           rast <osgeo.gdal.Dataset>: open raster
           n_bands <int>: number of bands in file (default=1)
        """
        # get nodata value
        r_a = rast.GetRasterBand(n_bands)
        r_nd = r_a.GetNoDataValue()

        # read raster as array
        rast_arr = np.array(r_a.ReadAsArray())

        # mask nodata value, if it exists
        if r_nd:
            rast_arr = np.ma.masked_where(rast_arr == r_nd, rast_arr)
            logging.info("NoData value: {0}".format(r_nd))
        else:
            rast_arr = r_a
            logging.info("NoData value could not be determined.")

        return (rast_arr,r_nd)

    '''
    @staticmethod
    def read_bip_as_array(rast, band_number):
        """Read band interleaved by pixel (BIP) file as array.

        Args:
            rast <osgeo.gdal.Dataset>: open raster
            band_number <int>: specific band number to grab from file
        """
        # get nodata value
        r_a = rast.GetRasterBand(band_number)
        r_nd = r_a.GetNoDataValue()

        # read raster as array
        rast_arr = np.array(rast.GetRasterBand(band_number).ReadAsArray())
        return rast_arr
    '''

class RasterCmp:
    @staticmethod
    def compare_proj_ref(test, mast):
        """Make sure projections are the same between two GDAL objects.

        Args:
            test <osgeo.gdal.Dataset>: test raster
            mast <osgeo.gdal.Dataset>: master raster
        """
        tst_proj = test.GetProjectionRef()
        mst_proj = mast.GetProjectionRef()

        proj_diff = (tst_proj == mst_proj)

        if proj_diff:
            logging.info("Projections match.")
            status = True
        else:
            logging.error("Projections do not match.")
            logging.error("Test transform: {0}".format(tst_proj))
            logging.error("Master transform: {0}".format(mst_proj))
            status = False

        return status

    @staticmethod
    def compare_geo_trans(test, mast):
        """Make sure geographic transforms are the same between GDAL objects.

        Args:
            test <osgeo.gdal.Dataset>: test raster
            mast <osgeo.gdal.Dataset>: master raster
        """
        tst_gt = test.GetGeoTransform()
        mst_gt = mast.GetGeoTransform()
        gt_diff = (tst_gt == mst_gt)
        if gt_diff:
            logging.info("Geo transforms match.")
            status = True
        else:
            logging.error("Geo transforms match.")
            logging.error("Test transform: {0}".format(tst_gt))
            logging.error("Master transform: {0}".format(mst_gt))
            status = False

        return status

    @staticmethod
    def extent_diff_cols(test, mast):
        """Make sure number of columns are the same between GDAL objects.

        Args:
            test <osgeo.gdal.Dataset>: test raster
            mast <osgeo.gdal.Dataset>: master raster
        """
        cols_diff = test.RasterXSize - mast.RasterXSize
        if cols_diff == 0:
            logging.info("Columns match.")
            status = True
        else:
            logging.error("Columns do not match.")
            logging.error("Test col: {0}".format(test.RasterXSize))
            logging.error("Master col: {0}".format(mast.RasterXSize))
            status = False

        return status

    @staticmethod
    def extent_diff_rows(test, mast):
        """Make sure number of rows are the same between GDAL objects.

        Args:
            test <osgeo.gdal.Dataset>: test raster
            mast <osgeo.gdal.Dataset>: master raster
        """
        rows_diff = test.RasterYSize - mast.RasterYSize
        if rows_diff == 0:
            logging.info("Rows match.")
            status = True
        else:
            logging.error("Rows do not match.")
            logging.error("Test row: {0}".format(test.RasterYSize))
            logging.error("Master row: {0}".format(mast.RasterYSize))
            status = False

        return status
