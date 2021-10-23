from threading import Thread
import cv2
from annotator.annotation_component import BoundingBox


class AnnotationPrediction:
    context = None
    vid_cap = None
    n_id = None
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
              frame_limit: int,
              n_id: str):
        cv2_bounding_box = self.convert_bounding_box_to_cv2_bnd_box(bounding_box)
        if cv2_bounding_box[2] == 0 or cv2_bounding_box[3] == 0:
            return False
        self.context = context
        self.vid_start_frame = vid_start_frame
        self.vid_frame_per_annotation_frame = vid_frame_per_annotation_frame
        self.prediction_frame_limit = frame_limit
        self.n_id = n_id
        # Initialize tracker components
        self.vid_cap = cv2.VideoCapture(vid_path)
        self.vid_frame_length = self.vid_cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, vid_start_frame)
        self._create_tracker(cv2_bounding_box)

        # Run on separate thread
        Thread(target=self._start_tracking, args=()).start()
        return True

    def on_complete_prediction(self, context, result, n_id):
        pass

    def _create_tracker(self, cv2_bounding_box):
        self.tracker = cv2.TrackerKCF_create()
        if self.vid_cap.isOpened():
            has_frames, img = self.vid_cap.read()
            if has_frames:
                self.tracker.init(img, cv2_bounding_box)

    def _start_tracking(self):
        if self.vid_cap is None or not self.vid_cap.isOpened():
            self.on_complete_prediction(self.context, ValueError('video not found'))
            return

        result = {}
        annotation_frame_counter = 0

        while True:
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

        self.on_complete_prediction(self.context, result, self.n_id)
        self.vid_cap.release()

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
