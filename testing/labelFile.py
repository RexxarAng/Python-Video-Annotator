from label.pascal_voc_io import PascalVocWriter, XML_EXT
from enum import Enum
import os.path
import collections


class LabelFileError(Exception):
    pass


class LabelFile(object):
    # It might be changed as window creates. By default, using XML ext
    # suffix = '.lif'
    suffix = XML_EXT

    def __init__(self, filename=None):
        self.shapes = ()
        self.filename = filename
        self.video_path = None
        self.image_data = None
        self.verified = False
        self.xml_file_path = None

    def save_pascal_voc_format(self, filename, annotations, video_path, image_shape, line_color=None, fill_color=None,
                               database_src=None):
        filename += ".xml"
        video_folder_path = os.path.dirname(video_path)
        video_folder_name = os.path.split(video_folder_path)[-1]
        video_file_name = os.path.basename(video_path)
        writer = PascalVocWriter(video_folder_name, video_file_name,
                                 image_shape, local_vid_path=video_path)
        writer.verified = self.verified
        annotations = collections.OrderedDict(sorted(annotations.items()))
        for frame in annotations:
            frame_object = []
            for annotation in annotations[frame]:
                label = annotation[0]
                bnd_box = annotation[1]
                # bnd_box = LabelFile.convert_cv2_bnd_box_to_points(annotation[1])
                verified = annotation[2]
                frame_object.append([bnd_box, label, frame, verified])
            writer.add_bnd_box_frame(frame_object)
        if annotations:
            writer.save(target_file=filename)
        return

    @staticmethod
    def toggle_verify(filename, frame, video_path, image_shape):
        filename += ".xml"
        video_folder_path = os.path.dirname(video_path)
        video_folder_name = os.path.split(video_folder_path)[-1]
        video_file_name = os.path.basename(video_path)
        writer = PascalVocWriter(video_folder_name, video_file_name,
                                 image_shape, local_vid_path=video_path)
        writer.toggle_verify(frame, filename)

    @staticmethod
    def is_label_file(filename):
        file_suffix = os.path.splitext(filename)[1].lower()
        return file_suffix == LabelFile.suffix

    @staticmethod
    def convert_points_to_bnd_box(points):
        x_min = float('inf')
        y_min = float('inf')
        x_max = float('-inf')
        y_max = float('-inf')
        for p in points:
            x = p[0]
            y = p[1]
            x_min = min(x, x_min)
            y_min = min(y, y_min)
            x_max = max(x, x_max)
            y_max = max(y, y_max)

        # Martin Kersner, 2015/11/12
        # 0-valued coordinates of BB caused an error while
        # training faster-rcnn object detector.
        if x_min < 1:
            x_min = 1

        if y_min < 1:
            y_min = 1

        return int(x_min), int(y_min), int(x_max), int(y_max)

    @staticmethod
    def convert_cv2_bnd_box_to_points(bnd_box):
        x_min = bnd_box[0]
        y_min = bnd_box[1]
        x_max = x_min + bnd_box[2]
        y_max = y_min + bnd_box[3]

        return int(x_min), int(y_min), int(x_max), int(y_max)
