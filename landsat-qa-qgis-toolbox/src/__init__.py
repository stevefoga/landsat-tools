# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LandsatQATools
                                 A QGIS plugin
 Decode Landsat QA bands.
                             -------------------
        begin                : 2017-05-17
        copyright            : (C) 2017 by Steve Foga, SGT Inc., Contractor to USGS EROS Center
        email                : steven.foga.ctr@usgs.gov
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load LandsatQATools class from file LandsatQATools.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .decode_qa import LandsatQATools
    return LandsatQATools(iface)
