import os
import simplejson as json
import csv
from qgis.core import *
from qgis.gui import *
from qgis.utils import *


class list_iterator(object):
    """List iterator to get Next and Previous items

    Args:
        object (_type_): _description_
    """

    def __init__(self, collection):
        self.collection = collection
        self.index = 0

    def next(self):
        try:
            result = self.collection[self.index]
            self.index += 1
        except IndexError:
            raise StopIteration
        return result

    def prev(self):
        self.index -= 1
        if self.index < 0:
            raise StopIteration
        return self.collection[self.index]

    def __iter__(self):
        return self


def set_file_pairs(chips_directory, input_label_directory):
    """
    set image and label file pairs tif and geojson
    """
    list_files = os.listdir(chips_directory)
    # extract image names and construct the paths of the label files
    chip_basename_files = [os.path.splitext(cfile)[0] for cfile in list_files if cfile.endswith(".tif")]
    file_pairs = []
    missing_label_files = []
    for chip_basename in chip_basename_files:
        geojson_label_file = os.path.join(input_label_directory, f"{chip_basename}.geojson")
        if not os.path.exists(geojson_label_file):
            # raise FileNotFoundError(f"Missing geojson file: {geojson_label_file}")
            missing_label_files.append(geojson_label_file)
        else:
            file_pairs.append((chip_basename))
    file_pairs.sort()
    return list_iterator(file_pairs), len(file_pairs), missing_label_files


def get_file_basename(filename):
    file_path, file_name = os.path.split(filename)
    file_basename, file_ext = os.path.splitext(file_name)
    return file_path, file_basename, file_ext


def display_info_alert(title, body, time):
    if title is None:
        title = "Info:"
    iface.messageBar().pushMessage(title, body, level=Qgis.Info, duration=time)


def display_warning_alert(title, body, time):
    if title is None:
        title = "Warning:"
    iface.messageBar().pushMessage(title, body, level=Qgis.Warning, duration=time)


def save_labels_to_output_dir(label_geojson_file, output_label_directory, vlayer):
    """Save puput geojson files."""
    _, file_basename, file_ext = get_file_basename(label_geojson_file)
    output_geojson_file = os.path.join(output_label_directory, f"{file_basename}{file_ext}")
    if os.path.exists(output_geojson_file):
        os.remove(output_geojson_file)
    QgsVectorFileWriter.writeAsVectorFormat(vlayer, output_geojson_file, "utf-8", vlayer.crs(), "GeoJSON")
    vlayer.rollBack()
    return


def write_json_missing_records(status_json_file, list_miss_records):
    """Write a json file of the missing labels"""
    if status_json_file == None:
        print("json output file not defined")
    with open(status_json_file, "w") as outfile:
        outfile.write("\n".join(list_miss_records))
    return


def write_status_records_csv(output_csv_status_file, json_records):
    """Write csv status file."""
    if os.path.exists(output_csv_status_file):
        os.remove(output_csv_status_file)
    # Write the csv file
    if len(json_records) == 0:
        return
    keys = json_records[0].keys()
    with open(output_csv_status_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        for json_recoord in json_records:
            writer.writerow(json_recoord)
    return


def read_status_records(output_csv_status_file):
    """Read status file when restart the task."""
    json_records = {}
    # Return empty list
    if not os.path.exists(output_csv_status_file):
        return json_records
    else:
        with open(output_csv_status_file, "r") as csvfile:
            datareader = csv.reader(csvfile)
            for index, row in enumerate(datareader):
                if index != 0 and len(row) > 0:
                    chip_id, accept, comment = row
                    json_records[chip_id] = {
                        "chip_id": chip_id,
                        "accept": json.loads(accept.lower()),
                        "comment": comment,
                    }
        return json_records


def check_folder(records_directory, chips_directory, input_label_directory, output_label_directory):
    """Check import folders."""
    flag = False
    if "".__eq__(records_directory) or not os.path.isdir(records_directory):
        flag = True
        display_warning_alert("Missing Record directory", "Select a existing record directory", 5)

    if "".__eq__(chips_directory) or not os.path.isdir(chips_directory):
        flag = True
        display_warning_alert("Missing Chips directory", "Select a existing chips directory", 5)

    if "".__eq__(input_label_directory) or not os.path.isdir(input_label_directory):
        flag = True
        display_warning_alert(
            "Missing Imput Label directory",
            "Select a existing imput label directory",
            5,
        )

    if "".__eq__(output_label_directory) or not os.path.isdir(output_label_directory):
        flag = True
        display_warning_alert(
            "Missing Opuput Labels directory",
            "Select a existing output label directory",
            5,
        )
    return flag


def clone_vlayer(vlayer):
    """Clone vector layer in memory"""
    layer_type = {"0": "Point", "1": "LineString", "2": "Polygon"}
    if str(vlayer.geometryType()) in layer_type.keys():
        str_source = layer_type[str(vlayer.geometryType())] + "?crs=epsg:" + str(vlayer.source())
    else:
        str_source = "Polygon"
    mem_layer = QgsVectorLayer(str_source, vlayer.name(), "memory")
    feats = [feat for feat in vlayer.getFeatures()]
    mem_layer_data = mem_layer.dataProvider()
    attr = vlayer.dataProvider().fields().toList()
    mem_layer_data.addAttributes(attr)
    mem_layer.updateFields()
    mem_layer_data.addFeatures(feats)
    return mem_layer
