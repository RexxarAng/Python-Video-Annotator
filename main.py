from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.label import Label
from kivymd.uix.list import MDList, OneLineIconListItem
from kivymd.uix.button import MDRectangleFlatButton
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.filemanager import MDFileManager
from kivy.factory import Factory
from kivymd.toast import toast
from kivy.core.window import Window
from kivy.uix.modalview import ModalView
import cv2
import numpy as np

# class VideoScreen(Screen):
#     image = ObjectProperty()
        

class NavigationLayout():
    pass

class ContentNavigationDrawer(BoxLayout):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()

class VideoAnnotatorApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.manager = None

    def build(self):
        # self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.primary_hue = "A700"
        self.theme_cls.accent_palette = "Teal"
        # Builder.load_file("videoscreen.kv")
        return Builder.load_file("main.kv")

    def file_manager_open(self):
        if not self.manager:
            self.manager = ModalView(size_hint=(1, 1), auto_dismiss=False)
            self.file_manager = MDFileManager(
                exit_manager=self.exit_manager, select_path=self.select_path)
            self.manager.add_widget(self.file_manager)
            self.file_manager.show('/')  # output manager to the screen
        self.manager_open = True
        self.manager.open()

    def exit_manager(self):
        self.manager.dismiss()
        self.manager_open = False

    def select_path(self, path):
        print(path)
        toast(path)
        self.exit_manager()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    def openVideo(self):
        vidcap = cv2.VideoCapture('video.mp4')
        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))-1
        currenttrackbar = 0
        def onChange(trackbarValue):
            global currenttrackbar 
            currenttrackbar = trackbarValue
            print(currenttrackbar)
            vidcap.set(cv2.CAP_PROP_POS_FRAMES,trackbarValue)
            err,img = vidcap.read()
            cv2.imshow("Label Video", img)
            pass
        
        # Update trackbar
        def onLeftArrow(k):
            global currenttrackbar
            if k == 2424832:
                if currenttrackbar > 0:
                    currenttrackbar -= 1
                    cv2.setTrackbarPos('start', 'Label Video', currenttrackbar)
        
        def onRightArrow(k):
            global currenttrackbar
            if k == 2555904:
                if currenttrackbar < length:
                    currenttrackbar += 1
                    cv2.setTrackbarPos('start', 'Label Video', currenttrackbar)

        cv2.namedWindow('Label Video')
        cv2.createTrackbar( 'start', 'Label Video', 0, length, onChange )
        cv2.createTrackbar( 'end'  , 'Label Video', length, length, onChange )


        onChange(0)

        start = cv2.getTrackbarPos('start','Label Video')
        end   = cv2.getTrackbarPos('end','Label Video')

        if start >= end:
            raise Exception("start must be less than end")
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,start)
        image_annotations = {}
        while(vidcap.isOpened()):
            hasFrames, img = vidcap.read()
            if hasFrames:
                if currenttrackbar in image_annotations:
                    print(image_annotations)
                cv2.imshow("Label Video", img)
                k = cv2.waitKeyEx(0) 
                # Update trackbar for 'left arrow'
                onLeftArrow(k)
                # Update trackbar for 'right arrow'        
                onRightArrow(k)
                if currenttrackbar == length:
                    k = cv2.waitKey(0)
                    onLeftArrow(k)
                    onRightArrow(k)
                    
                if k == ord('t'):
                    border_box = cv2.selectROI("Label Video", img, False)
                    selected_box = img[int(border_box[1]):int(border_box[1]+border_box[3]), int(border_box[0]):int(border_box[0]+border_box[2])]
                    cv2.imshow("ROI", selected_box)
                    if cv2.getTrackbarPos('start', 'Label Video') in image_annotations:
                        image_annotations[cv2.getTrackbarPos('start', 'Label Video')] = border_box
                    else:
                        image_annotations[cv2.getTrackbarPos('start', 'Label Video')] = border_box
                if k == 81 or k == 113:
                    break
                
                if cv2.getWindowProperty('Label Video', cv2.WND_PROP_VISIBLE) <1:
                    break
            else:
                break

        vidcap.release()
        cv2.destroyAllWindows()
        # print(self.root.ids)
        # self.root.ids.image.source = str(vidFrames[0])




if __name__ == "__main__":
    VideoAnnotatorApp().run()