# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LandsatQATools
                                 A QGIS plugin
 Decode Landsat QA bands.
                              -------------------
        begin                : 2017-05-17
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
# Initialize Qt resources from file resources.py
# import resources
# Import the code for the dialog
from decode_qa_dialog import LandsatQAToolsDialog
import lookup_dict
import os
import sys
from random import randint
import numpy as np
from osgeo import gdal, gdalconst
from qgis.core import *


class LandsatQATools:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'LandsatQATools_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Landsat QA QGIS Tools')
        self.toolbar = self.iface.addToolBar(u'LandsatQATools')
        self.toolbar.setObjectName(u'LandsatQATools')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('LandsatQATools', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = LandsatQAToolsDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        # Configure "Browse" button
        self.dlg.rasterBox.clear()
        self.dlg.browseButton.clicked.connect(self.select_output_file)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/LandsatQATools/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Decode QA'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr(u'&Landsat QA QGIS Tools'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def select_output_file(self):
        """
        Enables ability to browse file system for input file.
        :return:
        """
        filename = QFileDialog.getOpenFileName(self.dlg, "Select input file ",
                                               "", '*')
        self.dlg.rasterBox.addItem(filename)

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()

        # add all raster layers in current session to UI as potential inputs
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayer.RasterLayer:
                self.dlg.rasterBox.addItem(layer.name(), layer)

        # Run the dialog event loop
        result = self.dlg.exec_()

        # TODO: add logic to auto-detect band and sensor using input_raster

        # See if OK was pressed
        if result:
            # get variable names from input
            input_raster = str(self.dlg.rasterBox.currentText())
            band = str(self.dlg.bandBox.currentText())
            sensor = str(self.dlg.sensorBox.currentText())
            rm_low = self.dlg.rmLowBox.isChecked()

            # use gdal to get unique values
            ds = gdal.Open(input_raster)
            rb = ds.GetRasterBand(1)
            values = sorted(list(np.unique(np.array(rb.ReadAsArray()))))
            #ds = None

            # define lookup table
            bit_flags = lookup_dict.bit_flags
            #qa_values = lookup_dict.qa_values

            # convert input_sensor to sensor values used in qa_values
            if sensor == "Landsat 4-5, 7":
                sens = "L47"
            elif sensor == "Landsat 8":
                sens = "L8"
            else:
                sys.exit("Incorrect sensor provided. Input: {0}; Potential "
                         "options: Landsat 4-5, 7; Landsat 8"
                         .format(sensor))

            # get all possible bit values for sensor and band combination
            bit_values = sorted(bit_flags[band][sens].values())
            qa_labels = []
            for row in values:
                bit_bool = []
                for bv in bit_values:
                    if len(bv) == 1:  # single bit
                        bit_bool.append(row & 1 << bv[0] > 0)

                    elif len(bv) > 1:  # 2+ bits
                        bits = []
                        for b in bv:
                            bits.append(row & 1 << b > 0)
                        if all(item == True for item in bits):
                            bit_bool.append(True)
                        else:
                            bit_bool.append(False)

                    else:
                        sys.exit("No valid bits found for target band.")

                '''
                NEW logic for getting labels using bit wise dictionary
                '''
                # create description of each value based upon all possible bits
                true_bits = [i for (i, bb) in zip(bit_values, bit_bool) if bb]

                # if double bits exist, eliminate single bit descriptions,
                #   otherwise, the descriptions will duplicate themselves.
                bb_double = [len(i) > 1 for i in true_bits]
                if any(bb_double):
                    # get only the double bits
                    dbit_nest = [i for (i, db) in zip(true_bits, bb_double)
                                 if db]

                    # collapse the bits into a single list
                    dbits = [item for sublist in dbit_nest for item in sublist]

                    # remove matching single bits out of true_bits list
                    tbo = []
                    for t in true_bits:
                        tb_out = []
                        for d in dbits:
                            if t[0] != d or len(t) > 1:
                                tb_out.append(True)
                            else:
                                tb_out.append(False)
                        if all(tb_out):
                            tbo.append(t)

                    # replace true_bits with filtered list
                    true_bits = tbo

                def get_label(bits):
                    """
                    Generate label for value in attribute table.

                    :param bits: <list> List of True or False for bit position
                    :return: <str> Attribute label
                    """
                    if len(bits) == 0:
                        if band == 'radsat_qa':
                            return 'No Saturation'

                        elif band == 'sr_cloud_qa' or band == 'sr_aerosol':
                            return 'None'

                        elif band == 'BQA':
                            return 'Not Determined'

                    # build description from all bits represented in value
                    desc = []
                    for tb in bits:
                        k = next(key for key, value in
                                 bit_flags[band][sens].items() if value == tb)

                        # if 'low' labels are disabled, do not add them here
                        if rm_low and band != 'BQA' and 'low' in k.lower():
                            continue

                        # if last check, and not radiometric sat, set to 'clear'
                        elif rm_low and band == 'BQA' and 'low' in k.lower() \
                                and tb == bits[-1] and \
                                        'radiometric' not in k.lower() and \
                                not desc:
                            k = 'Clear'

                        # if BQA and bit is low radiometric sat, keep it
                        elif rm_low and band == 'BQA' and 'low' in k.lower():
                            if 'radiometric' not in k.lower():
                                continue

                        # if radsat_qa, handle differently to display cleaner
                        if band == 'radsat_qa':
                            if not desc:
                                desc = "Band {0} Data Saturation".format(tb[0])

                            else:
                                desc = "{0},{1} Data Saturation".format(
                                    desc[:desc.find('Data') - 1], tb[0])

                        # string creation for all other bands
                        else:
                            if not desc:
                                desc = "{0}".format(k)

                            else:
                                desc += ", {0}".format(k)

                    # final check to make sure something was set
                    if not desc:
                        desc = 'ERROR: bit set incorrectly'

                    return desc

                # add desc to row description
                qa_labels.append(get_label(true_bits))

            '''
            OLD logic for getting lookup values

            # use unique raster values (and sensor+band pair) to get defs
            if band == 'radsat_qa':
                qa_labels = {i:qa_values[band][i] for i in qa_values[band] if i
                             in list(values)}

            elif band == 'pixel_qa' and sens == 'L8':  # terrain occl. check
                qa_labels = {}
                for i in qa_values[band]:
                    if i >= 1024:
                        qa_labels[i] = 'Terrain occlusion'
                    else:
                        qa_labels[i] = qa_values[band][sens][i]

            else:
                qa_labels = {i:qa_values[band][sens][i] for i in
                             qa_values[band][sens] if i in list(values)}

            '''

            '''
            Use gdal.RasterAttributeTable to embed qa values in raster
            '''
            # create table
            rat = gdal.RasterAttributeTable()

            # get column count (for indexing columns)
            rat_cc = rat.GetColumnCount()

            # add 'value' and 'descr' columns to table
            rat.CreateColumn("Value", gdalconst.GFT_Integer,
                             gdalconst.GFU_MinMax)
            rat.CreateColumn("Descr", gdalconst.GFT_String,
                             gdalconst.GFU_MinMax)

            # populate table with contents of 'qa_labels'
            uid = 0
            for val, lab in zip(values, qa_labels):

                # 'value' column
                rat.SetValueAsInt(uid, rat_cc, int(val))

                # 'descr' column
                rat.SetValueAsString(uid, rat_cc + 1, lab)

                uid += 1

            # set raster attribute table to raster
            rb.SetDefaultRAT(rat)


            '''
            METHOD 1: use RasterAttributeTable to display values.

            QGIS' UI does not currently support reading Attribute Tables
            embedded in raster datasets. Instead, we'll assign labels and
            random colors to the raster's color palette in the QGIS UI.

            Feature request: https://issues.qgis.org/issues/4321

            # open raster with QGIS API
            q_raster = QgsRasterLayer(input_raster,
                                      os.path.basename(input_raster))
            # make sure the raster is valid
            if not q_raster.isValid():
                sys.exit("Layer {0} not valid!".format(input_raster))


            # save changes and close raster
            ds = None

            # add raster to QGIS interface
            QgsMapLayerRegistry.instance().addMapLayer(q_raster)
            '''

            '''
            METHOD 2: re-assign colors in QGIS
            '''
            # open raster
            q_raster = QgsRasterLayer(input_raster,
                                      os.path.basename(input_raster))
            if not q_raster.isValid():
                sys.exit("Layer {0} not valid!".format(input_raster))

            # define color shader
            shader = QgsRasterShader()

            # define ramp for color shader
            c_ramp_shader = QgsColorRampShader()
            c_ramp_shader.setColorRampType(QgsColorRampShader.EXACT)

            # assign a random color to each value, and apply label
            c_ramp_vals = []
            for val, lab in zip(values, qa_labels):
                c_ramp_vals.append(QgsColorRampShader.
                                   ColorRampItem(
                    float(val),
                    QColor('#%06x' % randint(0, 2 ** 24)),
                    lab))

            # apply new color/label combo to color ramps
            c_ramp_shader.setColorRampItemList(c_ramp_vals)
            shader.setRasterShaderFunction(c_ramp_shader)

            # apply color ramps to raster
            ps_ramp = QgsSingleBandPseudoColorRenderer(q_raster.dataProvider(),
                                                       1, shader)
            q_raster.setRenderer(ps_ramp)

            # add raster to QGIS interface
            QgsMapLayerRegistry.instance().addMapLayer(q_raster)
