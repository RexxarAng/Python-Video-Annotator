from threading import Thread
import cv2
import os
from label.labelFile import LabelFile, LabelFileError
from label.pascal_voc_io import PascalVocReader
from pprint import pprint
from annotator.annotation_component import BoundingBox


class AnnotationPrediction:
    context = None
    vid_cap = None

    vid_start_frame: int
    vid_frame_length: int
    vid_frame_per_annotation_frame: int
    prediction_frame_limit: int

    tracker: cv2.Tracker

    def __init__(self, **kwargs):
        pass

    def start(self,
              context,
              vid_path: str,
              bounding_box: BoundingBox,
              vid_start_frame: int,
              vid_frame_per_annotation_frame: int,
              frame_limit: int):
        cv2_bounding_box = self.convert_bounding_box_to_cv2_bnd_box(bounding_box)
        self.context = context
        self.vid_start_frame = vid_start_frame
        self.vid_frame_per_annotation_frame = vid_frame_per_annotation_frame
        self.prediction_frame_limit = frame_limit

        # Initialize tracker components
        self.vid_cap = cv2.VideoCapture(vid_path)
        self.vid_frame_length = self.vid_cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, vid_start_frame)
        self._create_tracker(cv2_bounding_box)

        # Run on separate thread
        Thread(target=self._start_tracking, args=()).start()
        return self

    def on_complete_prediction(self, context, result):
        pass

    def _create_tracker(self, cv2_bounding_box):
        # self.tracker = cv2.TrackerCSRT_create()
        self.tracker = cv2.TrackerKCF_create()
        if self.vid_cap.isOpened():
            has_frames, img = self.vid_cap.read()
            if has_frames:
                self.tracker.init(img, cv2_bounding_box)
                # self.tracker.init(img, (10, 10, 10, 10))

    def _start_tracking(self):
        if self.vid_cap is None or not self.vid_cap.isOpened():
            self.on_complete_prediction(self.context, ValueError('video not found'))
            return

        result = {}
        annotation_frame_counter = 0

        while True:
            # Go to next frame
            # current_frame += self.vid_frame_per_annotation_frame
            # if current_frame >= self.vid_frame_length:
            #     break
            # self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

            # Parsing video
            has_frames, img = self.vid_cap.read()
            if not has_frames:
                break

            current_frame = self.vid_cap.get(cv2.CAP_PROP_POS_FRAMES)
            print('prediction ', current_frame)
            if current_frame % self.vid_frame_per_annotation_frame != 0:
                continue
            print('predicting')

            annotation_frame_counter += 1
            if annotation_frame_counter >= self.prediction_frame_limit:
                break

            # Parsing tracker
            has_tracked_frame, bounding_box = self.tracker.update(img)
            if not has_tracked_frame:
                break

            result[current_frame] = self.convert_cv2_bounding_box_to_bounding_box(bounding_box)

        self.on_complete_prediction(self.context, result)


    # TODO: To be deleted
    # def add_tracker(self, img, label, borderbox):
    #     self.tracker = cv2.TrackerCSRT_create()
    #     self.tracker.init(img, borderbox)
    #     self.trackers[self.tracker] = label
    #
    # def remove_tracker(self, tracker):
    #     self.trackers.pop(tracker)
    #
    # def get_tracked_img(self, img):
    #     image_annotations = []
    #     for tracker, label in self.trackers.items():
    #         has_frames, bbox = tracker.update(img)
    #         if has_frames:
    #             bbox = LabelFile.convert_cv2_bnd_box_to_points(bbox)
    #             annotation = [label, bbox, tracker]
    #             image_annotations.append(annotation)
    #     return image_annotations

    @staticmethod
    def convert_bounding_box_to_cv2_bnd_box(bounding_box: BoundingBox):
        x_min = bounding_box.min_x
        y_min = bounding_box.min_y
        width = bounding_box.max_x - bounding_box.min_x
        height = bounding_box.max_y - bounding_box.min_y
        return int(x_min), int(y_min), int(width), int(height)

    @staticmethod
    def convert_cv2_bounding_box_to_bounding_box(cv2_bounding_box):
        x_min = cv2_bounding_box[0]
        y_min = cv2_bounding_box[1]
        x_max = x_min + cv2_bounding_box[2]
        y_max = y_min + cv2_bounding_box[3]
        bounding_box = BoundingBox(bounding_box=(int(x_min), int(y_min), int(x_max), int(y_max)))
        return bounding_box


class AnnotationFile:
    label_file = None
    img = None

    def __init__(self, **kwargs):
        self.filepath = kwargs['filepath']
        self.img = kwargs['img']
        self.filename = os.path.splitext(self.filepath)[0]

    def save_annotations(self, annotations):
        print("try saving")
        image_annotations = {}
        for frame in annotations:
            for i in annotations[frame]:
                bbox = [i.min_x, i.min_y, i.max_x, i.max_y]
                label = i.name
                verified = False
                annotation = [label, bbox, verified]
                if i.frame in image_annotations:
                    image_annotations[int(i.frame)].append(annotation)
                else:
                    image_annotations[int(i.frame)] = [annotation]
        try:
            if self.label_file is None:
                self.label_file = LabelFile()
                self.label_file.verified = False
            self.label_file.save_pascal_voc_format(filename=self.filename, annotations=image_annotations,
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
