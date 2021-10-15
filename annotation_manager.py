import cv2
import os
from label.labelFile import LabelFile, LabelFileError
from label.pascal_voc_io import PascalVocReader
from pprint import pprint


class AnnotationPrediction:

    def __init__(self, **kwargs):
        self.tracker = cv2.TrackerCSRT_create()
        self.trackers = {}

    def add_tracker(self, img, label, borderbox):
        self.tracker = cv2.TrackerCSRT_create()
        self.tracker.init(img, borderbox)
        self.trackers[self.tracker] = label

    def remove_tracker(self, tracker):
        self.trackers.pop(tracker)

    def get_tracked_img(self, img):
        image_annotations = []
        for tracker, label in self.trackers.items():
            has_frames, bbox = tracker.update(img)
            if has_frames:
                bbox = LabelFile.convert_cv2_bnd_box_to_points(bbox)
                annotation = [label, bbox, tracker]
                image_annotations.append(annotation)
        return image_annotations


class AnnotationFile:
    label_file = None
    img = None

    def __init__(self, **kwargs):
        self.filepath = kwargs['filepath']
        self.img = kwargs['img']
        self.filename = os.path.splitext(self.filepath)[0]

    def save_annotations(self, annotations):
        print("try saving")
        # image_annotations = {}
        # for i in annotations:
        #     bbox = [i.min_x, i.min_y, i.max_x, i.max_y]
        #     label = i.name
        #     verified = False
        #     annotation = [label, bbox, verified]
        #     if i.frame in image_annotations:
        #         image_annotations[i.frame].append(annotation)
        #     else:
        #         image_annotations[i.frame] = [annotation]
        try:
            if self.label_file is None:
                self.label_file = LabelFile()
                self.label_file.verified = False
            self.label_file.save_pascal_voc_format(filename=self.filename, annotations=annotations,
                                                   video_path=self.filepath, image_shape=self.img.shape)

        except LabelFileError as e:
            print("Error!")
            return False

    def load_pascal_xml_by_filename(self, xml_path):
        if self.filepath is None:
            return
        if os.path.isfile(xml_path) is False:
            return

        t_voc_parse_reader = PascalVocReader(xml_path)
        image_annotations = t_voc_parse_reader.get_annotations()
        return image_annotations
        # shapes = t_voc_parse_reader.get_shapes();
        # self.load_labels(shapes)
        # self.canvas.verified = t_voc_parse_reader.verified
