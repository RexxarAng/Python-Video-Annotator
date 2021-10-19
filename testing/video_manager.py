import cv2
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import PySimpleGUI as sg
import os
from testing.labelFile import LabelFile, LabelFileError
from label.pascal_voc_io import PascalVocReader


class VideoManager:

    clock = None
    img = None
    label_file = None
    window_name = 'Annotate Video'

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
        self.play_speed = 50

    def start(self):
        xml_path = os.path.join(self.filepath, self.filename + '.xml')
        if os.path.isfile(xml_path):
            self.load_pascal_xml_by_filename(xml_path)

        cv2.namedWindow(self.window_name)
        cv2.createTrackbar('Frame', self.window_name, 0, self.length, self.on_change)
        cv2.createTrackbar('Delay', self.window_name, self.play_speed, 100, self.set_speed)
        start = cv2.getTrackbarPos('Frame', self.window_name)
        self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        self.clock = Clock.schedule_interval(self.loop, 1.0 / 30.0)

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

    def loop(self, *args):
        # Destroy window if user click on the x on the window
        if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
            self.stop_all_resources()
        if self.vid_cap.isOpened():
            has_frames, img = self.vid_cap.read()
            #   if annotated start tracking
            if has_frames:
                # print(self.image_annotations)
                # self.img = self.rescale_frame(img, percent=50)
                self.img = self.rescale_frame(img, percent=50)
                img = self.rescale_frame(img, percent=50)
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
                            annotation = [label, bbox, False]
                            if self.current_frame in self.image_annotations:
                                self.image_annotations[self.current_frame].append(annotation)
                            else:
                                annotations = [annotation]
                                self.image_annotations[self.current_frame] = annotations

                self.current_frame += 1
                cv2.setTrackbarPos('Frame', self.window_name, self.current_frame)
                cv2.imshow(self.window_name, img)
                self.widget.root.ids.image_frame = img
                buffer = cv2.flip(img, 0).tostring()
                texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
                self.widget.root.ids.image.texture = texture
                k = cv2.waitKeyEx(self.play_speed)
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
                # if k == ord('d'):
                #     self.popup_select()
                if k == ord('v'):
                    self.toggle_verify()
                if k == ord('s'):
                    self.trackers = {}
                    self.save_annotations()
                if k == ord('t'):
                    self.start_annotate()
                    # start_multiple_annotate()

                if k == 81 or k == 113:
                    self.stop_all_resources()

            else:
                return

    def set_speed(self, val):
        self.play_speed = max(val, 1)

    def on_change(self, trackbarValue):
        self.widget.root.ids.slider.value = trackbarValue
        if not (trackbarValue == self.current_frame):
            self.current_frame = trackbarValue
            self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, trackbarValue)

    # Update trackbar
    def on_left_arrow(self):
        if self.current_frame > 0:
            self.current_frame -= 1
            cv2.setTrackbarPos('Frame', self.window_name, self.current_frame)

    def on_right_arrow(self):
        if self.current_frame < self.length:
            self.current_frame += 1
            cv2.setTrackbarPos('Frame', self.window_name, self.current_frame)

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
            border_box = cv2.selectROI(self.window_name, self.img, False)
            # Check if border box is not all 0 (default selectRoi returns (0,0,0,0)) before prompting for object label
            if all(border_box):
                label_object = sg.popup_get_text("Enter the label for this object: ", default_text="Smoking")
                if label_object:
                    self.tracker = cv2.TrackerCSRT_create()
                    self.tracker.init(self.img, border_box)
                    self.trackers[self.tracker] = label_object
                    selected_box = self.img[int(border_box[1]):int(border_box[1] + border_box[3]),
                                   int(border_box[0]):int(border_box[0] + border_box[2])]
                    self.draw_rectangle(self.img, label_object, border_box)
                    cv2.imshow("ROI", selected_box)
                    current_annotation = [label_object, border_box, False]
                    if cv2.getTrackbarPos('Frame', self.window_name) in self.image_annotations:
                        self.image_annotations[cv2.getTrackbarPos('Frame', self.window_name)].append(current_annotation)
                    else:
                        annotation_list = [current_annotation]
                        self.image_annotations[cv2.getTrackbarPos('Frame', self.window_name)] = annotation_list
            else:
                more = False

    # def popup_select(self, select_multiple=False):
    #     layout = [[sg.Listbox(self.trackers.values(), key='_LIST_', size=(45, len(self.trackers)),
    #                           select_mode='extended' if select_multiple else 'single'
    #                           , bind_return_key=True), sg.OK("Delete")]]
    #     window = sg.Window('Delete tracker', layout=layout)
    #     event, values = window.read()
    #     window.close()
    #     del window
    #     if select_multiple or values['_LIST_'] is None:
    #         print(values)
    #         return
    #     else:
    #         return

    @staticmethod
    def draw_rectangle(image, label_name, coordinates):
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

    def toggle_verify(self, frame=17):
        try:
            if self.label_file is None:
                self.label_file = LabelFile()
            self.label_file.toggle_verify(filename=self.filename, frame=frame,
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
        self.image_annotations = t_voc_parse_reader.get_annotations()
        # shapes = t_voc_parse_reader.get_shapes();
        # self.load_labels(shapes)
        # self.canvas.verified = t_voc_parse_reader.verified

    def stop_all_resources(self):
        self.clock.release()
        self.vid_cap.release()
        print('stop_all_resources')

    def __del__(self):
        self.stop_all_resources()
        print('__del__ videomanager')
