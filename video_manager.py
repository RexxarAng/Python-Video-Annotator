import cv2
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import PySimpleGUI as sg
import pascal_voc_io
from labelFile import *
import os


class VideoManager:

    img = None
    label_file = None

    def __init__(self, **kwargs):
        self.widget = kwargs['context']
        self.filepath = kwargs['filepath']
        self.vid_cap = cv2.VideoCapture(self.filepath)
        self.length = int(self.vid_cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        self.current_frame = 0
        self.image_annotations = {}
        self.tracker = cv2.TrackerCSRT_create()
        self.trackers = {}
        self.widget.root.ids.slider.min = 0
        self.widget.root.ids.slider.max = self.length
        self.widget.root.ids.slider.step = 1
        self.filename = os.path.splitext(self.filepath)[0]

    def start(self):
        cv2.namedWindow('Label Video')
        cv2.createTrackbar('Frame', 'Label Video', 0, self.length, self.on_change)
        self.on_change(0)
        start = cv2.getTrackbarPos('Frame', 'Label Video')
        self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        Clock.schedule_interval(self.loop, 1.0/30.0)

    def loop(self, *args):
        if self.vid_cap.isOpened():
            has_frames, img = self.vid_cap.read()
            #   if annotated start tracking
            if has_frames:
                # self.img = self.rescale_frame(img, percent=50)
                self.img = img
                print(self.image_annotations)
                if self.current_frame in self.image_annotations:
                    annotations = self.image_annotations.get(self.current_frame)
                    for annotation in annotations:
                        label = annotation[0]
                        bbox = annotation[1]
                        self.draw_rectangle(img, label, bbox)
                else:
                    for tracker, label in self.trackers.items():
                        has_frames, bbox = tracker.update(img)
                        if has_frames:
                            self.draw_rectangle(img, label, bbox)
                            annotation = [label, bbox]
                            if self.current_frame in self.image_annotations:
                                self.image_annotations[self.current_frame].append(annotation)
                            else:
                                annotations = [annotation]
                                self.image_annotations[self.current_frame] = annotations

                self.current_frame += 1
                cv2.setTrackbarPos('Frame', 'Label Video', self.current_frame)
                cv2.imshow("Label Video", img)
                self.widget.root.ids.image_frame = img
                buffer = cv2.flip(img, 0).tostring()
                texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
                self.widget.root.ids.image.texture = texture
                k = cv2.waitKeyEx(1)
                if k == 32:  # Pause on space bar
                    k = cv2.waitKey(-1)

                # Update trackbar for 'left arrow'
                # elif k == 2424832:
                #     on_left_arrow()
                # elif k == 2555904:
                #     on_right_arrow()

                # Update trackbar for 'right arrow'
                # on_right_arrow(k)
                # if current_frame == length:
                #     k = cv2.waitKey(0)
                #     on_left_arrow(k)
                #     on_right_arrow(k)
                if k == ord('s'):
                    trackers = {}
                    self.save_annotations()
                if k == ord('t'):
                    self.start_annotate()
                    # start_multiple_annotate()

                if k == 81 or k == 113:
                    return

                if cv2.getWindowProperty('Label Video', cv2.WND_PROP_VISIBLE) < 1:
                    return
            else:
                return

    def on_change(self, trackbarValue):
        self.current_frame = trackbarValue
        self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, trackbarValue)
        self.widget.root.ids.slider.value = self.current_frame
        # err, image = vid_cap.read()
        # image = rescale_frame(image, percent=50)
        # cv2.imshow("Label Video", image)

    # Update trackbar
    def on_left_arrow(self):
        if self.current_frame > 0:
            self.current_frame -= 1
            cv2.setTrackbarPos('Frame', 'Label Video', self.current_frame)

    def on_right_arrow(self):
        if self.current_frame < self.length:
            self.current_frame += 1
            cv2.setTrackbarPos('Frame', 'Label Video', self.current_frame)

    @staticmethod
    def rescale_frame(frame, percent=75):
        width = int(frame.shape[1] * percent / 100)
        height = int(frame.shape[0] * percent / 100)
        dim = (width, height)
        return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

    def start_annotate(self):
        self.trackers = {}
        more = True
        while more:
            border_box = cv2.selectROI("Label Video", self.img, False)
            label_object = sg.popup_get_text("Enter the label for this object: ", default_text="Smoking")
            if label_object:
                self.tracker = cv2.TrackerKCF_create()
                self.tracker.init(self.img, border_box)
                self.trackers[self.tracker] = label_object
                selected_box = self.img[int(border_box[1]):int(border_box[1] + border_box[3]),
                               int(border_box[0]):int(border_box[0] + border_box[2])]
                self.draw_rectangle(self.img, label_object, border_box)
                cv2.imshow("ROI", selected_box)
                current_annotation = [label_object, border_box]
                if cv2.getTrackbarPos('Frame', 'Label Video') in self.image_annotations:
                    self.image_annotations[cv2.getTrackbarPos('Frame', 'Label Video')].append(current_annotation)
                else:
                    annotation_list = [current_annotation]
                    self.image_annotations[cv2.getTrackbarPos('Frame', 'Label Video')] = annotation_list
            else:
                more = False

    def draw_rectangle(self, image, label_name, coordinates):
        pt1 = (int(coordinates[0]), int(coordinates[1]))
        pt2 = (int(coordinates[0] + coordinates[2]), int(coordinates[1] + coordinates[3]))
        cv2.rectangle(image, pt1, pt2, (255, 255, 0), 2, 1)
        cv2.putText(image, label_name, (int(coordinates[0]), int(coordinates[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 255, 255), 2)

    def save_annotations(self):
        try:
            if self.label_file is None:
                self.label_file = LabelFile()
                self.label_file.verified = False
            self.label_file.save_pascal_voc_format(filename=self.filename, annotations=self.image_annotations, video_path=self.filepath, image_shape=self.img.shape)

        except LabelFileError as e:
            print("Error!")
            return False

    def __del__(self):
        self.vid_cap.release()
        cv2.destroyAllWindows()