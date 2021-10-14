from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.core.window import Window
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
import os
from video_manager import VideoManager
from screens.video_annotation_screen import VideoAnnotator
from kivy.uix.screenmanager import ScreenManager, Screen


class NavigationLayout:
    pass


class ContentNavigationDrawer(BoxLayout):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()


class VideoAnnotatorApp(MDApp):

    video_annotator = None

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
        self.filename = ''
        self.video_manager = None

    def build(self):
        # self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.primary_hue = "A700"
        self.theme_cls.accent_palette = "Teal"
        # Builder.load_file("videoscreen.kv")
        return Builder.load_file("main.kv")

    def on_start(self):
        # self.open_annotator()
        pass

    def file_manager_open(self):
        self.file_manager.show(os.path.abspath("../"))  # output manager to the screen
        self.manager_open = True

    def select_path(self, path):
        """It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        """
        self.filepath = path
        self.exit_manager()
        toast(path)
        # self.open_video()
        self.open_annotator()

    def exit_manager(self, *args):
        """Called when the user reaches the root of the directory tree."""

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        """Called when buttons are pressed on the mobile device."""

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    def open_video(self):
        self.video_manager = VideoManager(context=self, filepath=self.filepath)
        self.video_manager.start()

    def open_annotator(self):
        self.root.ids.nav_drawer.set_state("close")
        self.root.ids.screen_manager.current = "Annotator"
        self.video_annotator = VideoAnnotator()
        self.video_annotator.load_video(self.filepath)
        print(self.root.ids.annotator_screen)
        # self.root.ids.annotator_screen.remove_all_widgets()
        self.root.ids.annotator_screen.clear_widgets()
        self.root.ids.annotator_screen.add_widget(self.video_annotator)
        # self.video_annotator.start()


if __name__ == "__main__":
    VideoAnnotatorApp().run()
