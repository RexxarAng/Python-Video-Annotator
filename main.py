from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.label import Label
from kivymd.uix.list import MDList, OneLineIconListItem
from kivymd.uix.button import MDRectangleFlatButton
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.core.window import Window
from kivymd.uix.filemanager import MDFileManager
from kivy.factory import Factory
from kivymd.toast import toast
import cv2
import numpy as np
import os
import PySimpleGUI as sg


# class VideoScreen(Screen):
#     image = ObjectProperty()


class NavigationLayout:
    pass


class ContentNavigationDrawer(BoxLayout):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()


class VideoAnnotatorApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            ext=['.mp4']
        )
        self.filepath = ''

    def build(self):
        # self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.primary_hue = "A700"
        self.theme_cls.accent_palette = "Teal"
        # Builder.load_file("videoscreen.kv")
        return Builder.load_file("main.kv")

    def file_manager_open(self):
        self.file_manager.show(os.path.abspath("../"))  # output manager to the screen
        self.manager_open = True

    def select_path(self, path):
        '''It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        '''
        self.filepath = path
        self.exit_manager()
        toast(path)
        self.open_video()

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    def open_video(self):
        vid_cap = cv2.VideoCapture(self.filepath)
        length = int(vid_cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        current_frame = 0
        image_annotations = {}
        tracker = cv2.TrackerCSRT_create()
        # trackers = cv2.legacy.MultiTracker_create()
        is_tracking = False
        current_label = 'Smoking'

        def on_change(trackbarValue):
            nonlocal current_frame, is_tracking
            current_frame = trackbarValue
            vid_cap.set(cv2.CAP_PROP_POS_FRAMES, trackbarValue)
            err, image = vid_cap.read()
            image = rescale_frame(image, percent=50)
            cv2.imshow("Label Video", image)

        # Update trackbar
        def on_left_arrow():
            nonlocal current_frame
            if current_frame > 0:
                current_frame -= 1
                cv2.setTrackbarPos('Frame', 'Label Video', current_frame)

        def on_right_arrow():
            nonlocal current_frame
            if current_frame < length:
                current_frame += 1
                cv2.setTrackbarPos('Frame', 'Label Video', current_frame)

        def rescale_frame(frame, percent=75):
            width = int(frame.shape[1] * percent / 100)
            height = int(frame.shape[0] * percent / 100)
            dim = (width, height)
            return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

        def start_annotate():
            nonlocal tracker, current_label, is_tracking
            border_box = cv2.selectROI("Label Video", img, False)
            label = sg.popup_get_text("Enter the label for this object: ", default_text="Smoking")
            current_label = label
            if label:
                tracker = cv2.TrackerCSRT_create()
                tracker.init(img, border_box)
                is_tracking = True
                selected_box = img[int(border_box[1]):int(border_box[1] + border_box[3]),
                               int(border_box[0]):int(border_box[0] + border_box[2])]
                cv2.imshow("ROI", selected_box)
                current_annotation = [label, border_box]
                if cv2.getTrackbarPos('Frame', 'Label Video') in image_annotations:
                    image_annotations[cv2.getTrackbarPos('Frame', 'Label Video')].append(current_annotation)
                else:
                    annotation_list = [current_annotation]
                    image_annotations[cv2.getTrackbarPos('Frame', 'Label Video')] = annotation_list

        # def start_multiple_annotate():
        #     nonlocal tracker, current_label, is_tracking, trackers
        #     trackers = cv2.legacy.MultiTracker_create()
        #     more = True
        #     while more:
        #         border_box = cv2.selectROI("Label Video", img, False)
        #         label = sg.popup_get_text("Enter the label for this object: ", default_text="Smoking")
        #         if label:
        #             current_label = label
        #             tracker = cv2.legacy.TrackerCSRT_create()
        #             trackers.add(tracker, img, border_box)
        #             is_tracking = True
        #             selected_box = img[int(border_box[1]):int(border_box[1] + border_box[3]),
        #                            int(border_box[0]):int(border_box[0] + border_box[2])]
        #             cv2.imshow("ROI", selected_box)
        #             current_annotation = [label, border_box]
        #             if cv2.getTrackbarPos('Frame', 'Label Video') in image_annotations:
        #                 image_annotations[cv2.getTrackbarPos('Frame', 'Label Video')].append(current_annotation)
        #             else:
        #                 annotation_list = [current_annotation]
        #                 image_annotations[cv2.getTrackbarPos('Frame', 'Label Video')] = annotation_list
        #         else:
        #             more = False

        def draw_rectangle(image, label_name, coordinates):
            pt1 = (int(coordinates[0]), int(coordinates[1]))
            pt2 = (int(coordinates[0] + coordinates[2]), int(coordinates[1] + coordinates[3]))
            cv2.rectangle(image, pt1, pt2, (255, 255, 0), 2, 1)
            cv2.putText(image, label_name, (int(coordinates[0]), int(coordinates[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.75,
                        (0, 255, 255), 2)

        cv2.namedWindow('Label Video')
        cv2.createTrackbar('Frame', 'Label Video', 0, length, on_change)
        on_change(0)

        start = cv2.getTrackbarPos('Frame', 'Label Video')

        vid_cap.set(cv2.CAP_PROP_POS_FRAMES, start)

        while vid_cap.isOpened():
            has_frames, img = vid_cap.read()
            #   if annotated start tracking
            if has_frames:
                img = rescale_frame(img, percent=50)
                print(image_annotations)
                if is_tracking:
                    has_frames, bbox = tracker.update(img)
                    if current_frame in image_annotations:
                        annotations = image_annotations.get(current_frame)
                        for annotation in annotations:
                            label = annotation[0]
                            bbox = annotation[1]
                            draw_rectangle(img, label, bbox)
                    else:
                        draw_rectangle(img, current_label, bbox)
                        annotation = [current_label, bbox]
                        if current_frame in image_annotations:
                            image_annotations[current_frame].append(annotation)
                        else:
                            annotations = [annotation]
                            image_annotations[current_frame] = annotations

                current_frame += 1

                cv2.setTrackbarPos('Frame', 'Label Video', current_frame)
                cv2.imshow("Label Video", img)
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
                    is_tracking = False
                if k == ord('t'):
                    start_annotate()
                    # start_multiple_annotate()

                if k == 81 or k == 113:
                    break

                if cv2.getWindowProperty('Label Video', cv2.WND_PROP_VISIBLE) < 1:
                    break
            else:
                break

        vid_cap.release()
        cv2.destroyAllWindows()
        # print(self.root.ids)
        # self.root.ids.image.source = str(vidFrames[0])


if __name__ == "__main__":
    VideoAnnotatorApp().run()
