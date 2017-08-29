# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LandsatQATools
                                 A QGIS plugin
 Decode Landsat QA bands.
                              -------------------
        begin                : 2017-08-29
        git sha              : $Format:%H$
        author               : Steve Foga, SGT Inc., Contractor to USGS
                                EROS Center
        email                : steven.foga.ctr@usgs.gov
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QColor, QFileDialog
from osgeo import gdal, gdalconst
import numpy as np
from qgis.core import *

'''
This tool should ideally replicate functionality from Landsat QA ArcGIS
Toolbox's "Extract QA Bands" tool. Details: https://github.com/USGS-EROS/
landsat-qa-arcgis-toolbox.

Prototype UI: extract_bands_dialog_base.ui

Follow decode_qa.py for how to get UI linked up with the run script.

'''

# TODO: design GUI, then import it here

# TODO: import any other modules needed to do processing

# TODO: initiate class (see decode_qa.py for examples)

# TODO: initiate interface, menus, etc.

# TODO: create run() function, where the real work happens

    # Run the dialog event loop
    result = self.dlg.exec_()

    # See if OK was pressed
    if result:
        # use gdal to get unique values
        ds = gdal.Open(input_raster)
        rb = ds.GetRasterBand(1)
        values = sorted(list(np.unique(np.array(rb.ReadAsArray()))))

        # TODO: write logic to get information from GUI inputs

        # TODO: extract bit(s) based upon inputs, write to separate bands
        # TODO: optionally combine bands into single raster

