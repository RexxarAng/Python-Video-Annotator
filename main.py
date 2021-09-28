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
from kivymd_extensions.filemanager import FileManager
import cv2
import os

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
        current_trackbar = 0

        def on_change(trackbarValue):
            global current_trackbar
            current_trackbar = trackbarValue
            print(current_trackbar)
            vid_cap.set(cv2.CAP_PROP_POS_FRAMES, trackbarValue)
            err, image = vid_cap.read()
            cv2.imshow("Label Video", image)

        # Update trackbar
        def on_left_arrow(k):
            global current_trackbar
            if k == 2424832:
                if current_trackbar > 0:
                    current_trackbar -= 1
                    cv2.setTrackbarPos('start', 'Label Video', current_trackbar)

        def on_right_arrow(k):
            global current_trackbar
            if k == 2555904:
                if current_trackbar < length:
                    current_trackbar += 1
                    cv2.setTrackbarPos('start', 'Label Video', current_trackbar)

        cv2.namedWindow('Label Video')
        cv2.createTrackbar('start', 'Label Video', 0, length, on_change)
        cv2.createTrackbar('end', 'Label Video', length, length, on_change)

        on_change(0)

        start = cv2.getTrackbarPos('start', 'Label Video')
        end = cv2.getTrackbarPos('end', 'Label Video')

        if start >= end:
            raise Exception("start must be less than end")
        vid_cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        image_annotations = {}
        while vid_cap.isOpened():
            has_frames, img = vid_cap.read()
            if has_frames:
                if current_trackbar in image_annotations:
                    print(image_annotations)
                cv2.imshow("Label Video", img)
                k = cv2.waitKeyEx(0)
                # Update trackbar for 'left arrow'
                on_left_arrow(k)
                # Update trackbar for 'right arrow'
                on_right_arrow(k)
                if current_trackbar == length:
                    k = cv2.waitKey(0)
                    on_left_arrow(k)
                    on_right_arrow(k)

                if k == ord('t'):
                    border_box = cv2.selectROI("Label Video", img, False)
                    selected_box = img[int(border_box[1]):int(border_box[1] + border_box[3]),
                                   int(border_box[0]):int(border_box[0] + border_box[2])]
                    cv2.imshow("ROI", selected_box)
                    if cv2.getTrackbarPos('start', 'Label Video') in image_annotations:
                        image_annotations[cv2.getTrackbarPos('start', 'Label Video')] = border_box
                    else:
                        image_annotations[cv2.getTrackbarPos('start', 'Label Video')] = border_box
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