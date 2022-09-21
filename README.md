# Chippy Checker Editor

This is a lightweight QGIS (Quantum GIS) plugin that allows a systematic review of remote sensing image chips together with their geojson label files. Chip-label pairs may be accepted or rejected, and the QGIS vector editing tools may be used to make edits in any geojson label file.


Chips and labels are stored in local directories. The CCE plugin assumes that image chip files and label geojson files are contained in different directories, and that matching chip-label pairs have the same basename. For example '1893-0eef.tif' and '1893-0eef.geojson' are a matched chip-label pair.

The CCE plugin allows rapid local review and editing of training datasets for machine learning applications. It can be installed in QGIS via a downloaded zip file (instructions are below). 

# Installation of the CCE plugin

#### Download the ZIP plugin file from : https://github.com/developmentseed/chippy-checker-editor/archive/refs/heads/main.zip.

1. Click on `Plugins` -> `Manage and Install Plugins`.
2. Select the option  `Install from ZIP`. 
3. Select the zip file and click 'install', as shown in the gif below.

![2022-07-11 12 03 43_fixed](https://user-images.githubusercontent.com/1152236/178319413-f6dac886-8bcf-4645-8ecb-c932ebbbfabd.gif)

4. Start the CCE plugin by Clicking `Plugins` -> `Chippy Checker Editor`.

## Instructions for use

The plugin needs access to 4 directories, which are listed in the panel to the left of the main QGIS window. These are explained below.

![2022-07-11 12 16 50_fixed](https://user-images.githubusercontent.com/1152236/178321372-cc6d3f88-2067-4a1b-a495-285d18b52763.gif)


### Records directory

The plugin will create 2 files in the records directory, containing the output from the Chippy Checker Editor session. 

- `missing_labels.csv` - This file contains a list of missing label-geojson files.
- `chip_review.csv` - This file contains a list of reviewed chips, including their status (accepted or rejected). This allows the user to close the session, and then resume the review work later on.

### Chips directory

This folder should contain the image chips that need to be reviewed. E.g: [dataset/chips](dataset/chips)

### Input label directory

This folder should contain the label-geojson files. E.g: [dataset/labels](dataset/labels)

### Output label directory

This folder will store the output label-geojson files for *accepted* chip-label pairs. The geojson files in this directory will contain any label edits that were made before accepting the chip-label pair.

## Running CCE

Once you have set the directory paths as explained above, click `Load Task`. The first chip-label pair will be displayed. The vector labels file is automatically presented in 'edit' mode, so that you can make edits to the labels as desired.

Under the `Load Task` button, you will see a text box and buttons that say `Accept` and `Reject`. 

The text box is for any comments you have about the chip; these will be stored in the CSV file along with the chip's Accept/Reject status.

You have 3 options for each chip:

1. `Reject` the chip if you do not want to use it, and do not think it can be repaired with a few edits.
2. `Accept` the chip if it is ready to use.
3. Edit the chip labels using the QGIS vector editing tools, and then `Accept` the chip when you're done.

After clicking `Accept/Reject`, you will be driven to the next chip/label pair for review. 

If you need to close the session, you may do so at any time. If you restart the same session with the same directories, including the `Records` directory, the CCE plugin will read the CSV file and pick up your review work where you left off. 

## Licensing

Chippy Checker Editor QGIS Plugin: for reviewing georeferenced training data.
Copyright (C) 2022 DevGlobal Partners

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.