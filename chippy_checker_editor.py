# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ChippyCheckerEditor
                                 A QGIS plugin
 This a plugin to edit vector layer with chips as background.

 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-07-04
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Development Seed
        email                : ruben@developmentseed.org
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog

# Initialize Qt resources from file resources.py
from .resources import *

from qgis.core import *
from qgis.gui import *
from qgis.utils import *  # iface should be in here
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Import the code for the DockWidget
from .chippy_checker_editor_dockwidget import ChippyCheckerEditorDockWidget
from .chippy_checker_utils import (
    get_file_basename,
    display_info_alert,
    check_folder,
    save_labels_to_output_dir,
    write_json_missing_records,
    set_file_pairs,
    read_status_records,
    write_status_records_csv,
    clone_vlayer,
)

import os.path


class ChippyCheckerEditor:
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
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(self.plugin_dir, "i18n", "ChippyCheckerEditor_{}.qm".format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr("&Chippy Checker Editor")
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar("ChippyCheckerEditor")
        self.toolbar.setObjectName("ChippyCheckerEditor")

        # print "** INITIALIZING ChippyCheckerEditor"

        self.pluginIsActive = False
        self.dockwidget = None

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
        return QCoreApplication.translate("ChippyCheckerEditor", message)

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
        parent=None,
    ):
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
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ":/plugins/chippy_checker_editor/icon.png"
        self.add_action(
            icon_path,
            text=self.tr("Chippy Checker Editor"),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

    # --------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # Save progress in case plugin is close
        json_records_list = list(self.json_records.values())
        write_status_records_csv(self.output_csv_status_file, json_records_list)

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # print "** UNLOAD ChippyCheckerEditor"

        for action in self.actions:
            self.iface.removePluginMenu(self.tr("&Chippy Checker Editor"), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    ##### Select record inputs dir #####
    def select_input_records_dir(self):
        folder = str(QFileDialog.getExistingDirectory(self.dockwidget, "Select Records Directory"))
        self.dockwidget.lineEdit_Records.setText(folder)
        self.records_directory = folder

    ##### Select chips inputs dir #####
    def select_input_chips_dir(self):
        folder = str(QFileDialog.getExistingDirectory(self.dockwidget, "Select Chips Directory"))
        self.dockwidget.lineEdit_Chips.setText(folder)
        self.chips_directory = folder

    ##### Select output label dir #####
    def select_input_label_dir(self):
        folder = str(QFileDialog.getExistingDirectory(self.dockwidget, "Select Input Label Directory"))
        self.dockwidget.lineEdit_InputLabelDir.setText(folder)
        self.input_label_directory = folder

    ##### Select output label dir #####
    def select_output_label_dir(self):
        folder = str(QFileDialog.getExistingDirectory(self.dockwidget, "Select Output Label Directory"))
        self.dockwidget.lineEdit_OutputLabelDir.setText(folder)
        self.output_label_directory = folder

    def reset_chip(self, backward):
        """operations common to accepting and rejecting the previous chip

        Args:
            backward (Bool): Backwards if True
        """
        while True:
            try:
                if backward:
                    chip_id = self.chip_iterator.prev()
                    if chip_id == self.current_json_record["chip_id"]:
                        chip_id = self.chip_iterator.prev()
                else:
                    chip_id = self.chip_iterator.next()

            except StopIteration:
                if backward:
                    display_info_alert(None, "No more previous items", 5)
                else:
                    display_info_alert(None, "No more labels to edit", 5)

                return

            raster_file = os.path.join(self.chips_directory, f"{chip_id}.tif")
            if backward:
                vector_file = os.path.join(self.output_label_directory, f"{chip_id}.geojson")
                if not os.path.exists(vector_file):
                    vector_file = os.path.join(self.input_label_directory, f"{chip_id}.geojson")
            else:
                vector_file = os.path.join(self.input_label_directory, f"{chip_id}.geojson")

            if not self.chip_already_reviewed(chip_id, backward):
                break

        self.raster_file = raster_file
        self.vector_file = vector_file
        # QgsProject.instance().setDirty(False)

        # load chip, label into QGIS
        rlayer = iface.addRasterLayer(self.raster_file)
        _, file_basename, _ = get_file_basename(self.vector_file)
        vlayer = QgsVectorLayer(self.vector_file, file_basename, "ogr")
        vlayer = clone_vlayer(vlayer)

        self.vlayer = vlayer
        self.rlayer = rlayer

        QgsProject.instance().addMapLayer(vlayer)
        iface.setActiveLayer(vlayer)
        iface.mapCanvas().setExtent(rlayer.extent())
        iface.mapCanvas().zoomToFullExtent()
        activelayer = iface.activeLayer()
        # change style of vector layer
        myRenderer = activelayer.renderer()
        mySymbol1 = QgsFillSymbol.createSimple({"color": "255,0,0,0", "color_border": "#FF0000", "width_border": "0.4"})
        myRenderer.setSymbol(mySymbol1)
        activelayer.triggerRepaint()

        # toggle label editing
        iface.actionToggleEditing().trigger()

        # reset json record and comment box
        self.current_json_record = {}
        self.current_json_record["chip_id"] = chip_id
        # self.current_json_record["label"] = vector_file

        self.dockwidget.textEdit_CommentBox.setText("")
        self.dockwidget.textEdit_CommentBox.setPlaceholderText("Your Comment Here")
        return

    def chip_already_reviewed(self, chip_id, backward):
        reviewed_chips = self.json_records.keys()
        chip_was_reviwed = False
        if chip_id in reviewed_chips:
            chip_was_reviwed = True
        if backward:
            chip_was_reviwed = False
        return chip_was_reviwed

    ##### Select chips inputs dir #####
    def start_task(self):
        """Start reviewing chips."""
        # Clear all other layers
        QgsProject.instance().clear()

        records_directory = self.dockwidget.lineEdit_Records.text()
        chips_directory = self.dockwidget.lineEdit_Chips.text()
        input_label_directory = self.dockwidget.lineEdit_InputLabelDir.text()
        output_label_directory = self.dockwidget.lineEdit_OutputLabelDir.text()
        # records_directory = "/Users/ruben/Desktop/ramp_sierraleone_2022_05_31/assets"
        # chips_directory = "/Users/ruben/Desktop/ramp_sierraleone_2022_05_31/assets/source2"
        # input_label_directory = "/Users/ruben/Desktop/ramp_sierraleone_2022_05_31/assets/labels2"
        # output_label_directory = "/Users/ruben/Desktop/ramp_sierraleone_2022_05_31/assets/output2"

        if check_folder(records_directory, chips_directory, input_label_directory, output_label_directory):
            return

        self.raster_file = None
        self.vector_file = None

        self.chips_directory = records_directory
        self.chips_directory = chips_directory
        self.input_label_directory = input_label_directory
        self.output_label_directory = output_label_directory

        # Set records status file
        self.output_csv_status_file = os.path.join(records_directory, "chip_review.csv")
        self.output_missing_labels_file = os.path.join(records_directory, "missing_labels.csv")

        self.json_records = read_status_records(self.output_csv_status_file)

        # Init a empty record
        self.current_json_record = {}

        # Match files
        self.chip_iterator, self.number_chips, missing_label_files = set_file_pairs(chips_directory, input_label_directory)

        ## Set stats
        self.dockwidget.label_NumberChips.setText(str(self.number_chips))
        self.dockwidget.label_ReviewedChips.setText(str(len(list(self.json_records.keys()))))

        if len(missing_label_files) > 0:
            self.dockwidget.label_NumberMissingLabels.setText(str(len(missing_label_files)))
            write_json_missing_records(self.output_missing_labels_file, missing_label_files)
        # Start interacting
        self.reset_chip(False)

    def get_comment(self):
        """Get comment from extEdit

        Returns:
            str: comment
        """
        comment = self.dockwidget.textEdit_CommentBox.toPlainText()
        if comment is None:
            comment = ""
        return comment

    def save_action(self, action_status):
        """Save action either accepted or rejected

        Args:
            action_status (Bool): Action estatus
        """
        QgsProject.instance().clear()

        self.current_json_record["accept"] = action_status
        self.current_json_record["comment"] = self.get_comment()

        self.json_records[self.current_json_record["chip_id"]] = self.current_json_record

        self.current_json_record = {}
        # Write in json and csv file the status

        # Save multiples of 5 items
        json_records_list = list(self.json_records.values())

        write_status_records_csv(self.output_csv_status_file, json_records_list)

        self.dockwidget.label_ReviewedChips.setText(str(len(json_records_list)))

        self.reset_chip(False)
        return

    ############ Accept Action ############
    def accept_chip_action(self):
        # Export current layer to the output directory
        if self.iface.activeLayer() is not None:
            save_labels_to_output_dir(self.vector_file, self.output_label_directory, self.vlayer)
        print(f"ACCEPTED: {self.chips_directory}/{self.current_json_record['chip_id']}.tif")
        self.save_action(True)

    ############ Reject Action ############
    def reject_chip_action(self):
        print(f"REJECTED: {self.chips_directory}/{self.current_json_record['chip_id']}.tif")
        self.save_action(False)

    ############ backward Action ############
    def backward_chip_action(self):
        print(f"BACKWARD")
        QgsProject.instance().clear()
        self.reset_chip(True)

    def clean_directories(self):
        self.dockwidget.lineEdit_OutputLabelDir.setText("")
        self.dockwidget.lineEdit_Records.setText("")
        self.dockwidget.lineEdit_Chips.setText("")
        self.dockwidget.lineEdit_InputLabelDir.setText("")
        self.dockwidget.lineEdit_OutputLabelDir.setText("")

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            print("** STARTING ChippyCheckerEditor")
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = ChippyCheckerEditorDockWidget()
                self.dockwidget.pushButton_Records.clicked.connect(self.select_input_records_dir)
                self.dockwidget.pushButton_Chips.clicked.connect(self.select_input_chips_dir)
                self.dockwidget.pushButton_InputLabelDir.clicked.connect(self.select_input_label_dir)
                self.dockwidget.pushButton_OutputLabelDir.clicked.connect(self.select_output_label_dir)
                self.dockwidget.pushButton_LoadTask.clicked.connect(self.start_task)
                self.dockwidget.pushButton_AcceptChip.clicked.connect(self.accept_chip_action)
                self.dockwidget.pushButton_RejectChip.clicked.connect(self.reject_chip_action)
                self.dockwidget.pushButton_Backward.clicked.connect(self.backward_chip_action)

                self.dockwidget.closingPlugin

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
            QgsProject.instance().clear()
            # Clean directories
            self.clean_directories()