from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color
from kivy.metrics import dp
from kivy.uix.image import Image
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.gridlayout import MDGridLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.slider import MDSlider
from kivymd.icon_definitions import md_icons
from kivy.graphics.texture import Texture
import cv2
from enum import Enum
from annotator.annotation_canvas import (AnnotationCanvas)
from annotator.annotation_event import *
from annotation_manager import AnnotationFile

class VideoPlayBackMode(Enum):
    Stopped = 1
    Playing = 2


class VideoAnnotator(MDGridLayout):

    FRAME_COUNT = cv2.CAP_PROP_FRAME_COUNT

    _selected_label = 'smoking'

    annotation_canvas = None
    vid_path = None
    vid_cap = None
    vid_current_frame = 0
    vid_frame_length = 0
    vid_fps = 29
    play_speed = 1
    annotator_fps = 3
    img = None
    clock = None

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        kwargs['md_bg_color'] = (0.141, 0.153, 0.173, 1)
        super(VideoAnnotator, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.on_keyboard)  # bind our handler

        self.video_playback = VideoPlayBackMode.Stopped

        self.main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(.8, 1))
        self.add_widget(self.main_layout)

        self.side_dock = MDBoxLayout(
            orientation='vertical',
            # adaptive_height=True,
            size_hint_x=None,
            width=dp(180),
            md_bg_color=(0.181, 0.193, 0.213, 1))
        self.add_widget(self.side_dock)

        # Create Annotation Canvas
        self.annotation_canvas = AnnotationCanvas(
            size_hint=(1, .8))
        self.main_layout.add_widget(self.annotation_canvas)

        # Create Slider
        self.time_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, .1),
            size_hint_y=None,
            height=dp(120),
            md_bg_color=(0.181, 0.193, 0.213, 1)
        )
        self.main_layout.add_widget(self.time_layout)

        self.time_slider = MDSlider(
            color=(.6, .6, .6, 1))
        self.time_slider.hint_radius = 2
        self.time_slider.bind(on_touch_move=self.on_touch_up_timer_slider, on_touch_down=self.on_touch_up_timer_slider)
        # self.time_slider.bind(value=self.on_touch_up_timer_slider)
        self.time_layout.add_widget(self.time_slider)

        self.time_control_layout = MDBoxLayout(
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
            padding=[10, 10, 10, 10]
        )
        self.time_layout.add_widget(self.time_control_layout)
        self.time_control_layout.add_widget(MDIconButton(
            icon='skip-backward',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        ))
        self.time_control_play_button = MDIconButton(
            icon='play',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )
        # self.time_control_play_button.bind(on_touch_down=self.on_mouse_down_play_button)
        self.time_control_play_button.on_press = self.on_mouse_down_play_button
        self.time_control_layout.add_widget(self.time_control_play_button)
        self.time_control_layout.add_widget(MDIconButton(
            icon='skip-forward',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        ))

        # Create Annotation List
        self.side_dock.add_widget(MDLabel(
            text='Annotations',
            theme_text_color="Custom",
            size_hint_y=None,
            height=dp(50),
            halign='center',
            text_color=[1, 1, 1, 1]))
        self.annotation_scroll_view = ScrollView(
            size_hint=(1, 0.5)
        )
        self.annotation_list = MDList(
            size_hint=(1, 1)
            # md_bg_color=(0.241, 0.253, 0.273, 1)
        )
        self.annotation_scroll_view.add_widget(self.annotation_list)
        self.side_dock.add_widget(self.annotation_scroll_view)

        # Create Annotation List
        self.side_dock.add_widget(MDLabel(
            text='Labels',
            theme_text_color="Custom",
            size_hint_y=None,
            height=dp(50),
            halign='center',
            text_color=[1, 1, 1, 1]))
        self.label_scroll_view = ScrollView(
            size_hint=(1, 0.5)
        )
        self.side_dock.add_widget(self.label_scroll_view)
        self.label_list = MDList(
            size_hint=(1, 1),
            md_bg_color=(0.241, 0.253, 0.273, 1)
        )
        self.label_scroll_view.add_widget(self.label_list)
        self.annotation_canvas.subscribe_event(self.on_annotation_canvas_event)

    def load_video(self, video_path):
        self.vid_path = video_path
        self.vid_cap = cv2.VideoCapture(video_path)
        self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, 1)
        self.vid_fps = self.vid_cap.get(cv2.CAP_PROP_FPS)
        print('FPS')
        print(self.vid_fps)
        self.set_vid_frame_length(int(self.vid_cap.get(cv2.CAP_PROP_FRAME_COUNT) - 1))
        if self.vid_cap.isOpened():
            has_frames, img = self.vid_cap.read()
            self.img = img
            if has_frames:
                buffer = cv2.flip(img, 0).tostring()
                print(img.shape)
                texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
                self.annotation_canvas.texture = texture
                self.annotation_canvas.size_hint_x = None
                self.annotation_canvas.size_hint_y = None
                self.annotation_canvas.width = dp(img.shape[1])
                self.annotation_canvas.height = dp(img.shape[0])

    def set_vid_frame_length(self, video_frame):
        self.vid_frame_length = video_frame
        self.time_slider.max = self.convert_video_frame_to_annotator_frame(video_frame)

    def set_vid_current_frame(self, video_frame):
        print(video_frame)
        self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, video_frame)
        if self.vid_cap.isOpened():
            has_frames, img = self.vid_cap.read()
            if has_frames:
                buffer = cv2.flip(img, 0).tostring()
                print(img.shape)
                texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
                self.annotation_canvas.texture = texture
                self.vid_current_frame = video_frame
                self.time_slider.value = self.convert_video_frame_to_annotator_frame(video_frame)
                return True
        return False

    def play_video(self):
        # if self.clock is not None:
        #     Clock.unschedule(self.clock)
        #     self.clock = None
        self.video_playback = VideoPlayBackMode.Playing
        self.time_control_play_button.icon = 'stop'
        self.clock = Clock.schedule_interval(self.playing, 1.0 / self.vid_fps / self.play_speed)

    def playing(self, *args):
        print('playing')
        if not self.set_vid_current_frame(self.vid_current_frame+1):
            self.toggle_play()  # To stop playing when video reaches the end

    def stop_video(self):
        self.video_playback = VideoPlayBackMode.Stopped
        self.time_control_play_button.icon = 'play'
        if self.clock is not None:
            self.clock.release()
            self.clock = None

    def on_mouse_down_play_button(self):
        self.toggle_play()

    def toggle_play(self):
        if self.video_playback == VideoPlayBackMode.Stopped:
            self.play_video()
        else:
            self.stop_video()

    def convert_video_frame_to_annotator_frame(self, value: int):
        return int(value / self.vid_fps * self.annotator_fps)

    def convert_video_frame_from_annotator_frame(self, value):
        return int(value * self.vid_fps / self.annotator_fps)

    def on_touch_up_timer_slider(self, widget, touch, ):
        print(widget)
        print(touch)
        if widget.collide_point(*touch.pos):
            print('touched1')
            # Clock.schedule_once(self.on_timer_slider_update, 0.01)
            print(self.time_slider.value)
            self.set_vid_current_frame(self.convert_video_frame_from_annotator_frame(self.time_slider.value))

    def on_timer_slider_update(self, widget):
        print('touched2')
        self.stop_video()
        self.set_vid_current_frame(self.convert_video_frame_from_annotator_frame(self.time_slider.value))

    def on_annotation_canvas_event(self, event):
        # print(event)
        if isinstance(event, AnnotationCreatedEvent):
            event.annotation.list_item = OneLineListItem(
                text=event.annotation.name,
                theme_text_color='Custom',
                text_color='#EEEEEEFF'
            )
            self.annotation_list.add_widget(event.annotation.list_item)
        elif isinstance(event, AnnotationDeletedEvent):
            self.annotation_list.remove_widget(event.annotation.list_item)
        elif isinstance(event, AnnotationSelectedEvent):
            print('divider color')
            print(event.annotation.list_item.bg_color)
            for list_item in self.annotation_list.children:
                if isinstance(list_item, OneLineListItem):
                    list_item.bg_color = (0, 0, 0, 0)
            event.annotation.list_item.bg_color = (0, 1, 0, .5)

    def on_left_arrow(self):
        if self.current_frame > 0:
            self.current_frame -= 1
            cv2.setTrackbarPos('Frame', self.window_name, self.current_frame)

    def on_right_arrow(self):
        if self.current_frame < self.length:
            self.current_frame += 1
            cv2.setTrackbarPos('Frame', self.window_name, self.current_frame)

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        print(key)
        print(scancode)
        print(codepoint)
        print(modifier)
        if 'ctrl' in modifier and codepoint == 'z':
            self.annotation_canvas.remove_annotation_at_index(len(self.annotation_canvas.annotations) - 1)
        elif 'ctrl' in modifier and codepoint == 'a':
            self.annotation_canvas.set_mode_create_annotation('smoking')
        elif 'ctrl' in modifier and codepoint == 's':
            annotation_file = AnnotationFile(filepath=self.vid_path, img=self.img)
            annotation_file.save_annotations(self.annotation_canvas.annotations)
        elif key == 276:
            # Left Arrow
            self.annotation_canvas.move_left()
        elif key == 275:
            # Right Arrow
            self.annotation_canvas.move_right()
        elif key == 274:
            # Down Arrow
            self.annotation_canvas.move_down()
        elif key == 273:
            # Up Arrow
            self.annotation_canvas.move_up()
        elif key == 127 or key == 8:
            # Delete Key
            self.annotation_canvas.remove_selected_annotation()

    def __draw_shadow__(self, origin, end, context=None):
        pass
