from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color
from kivy.metrics import dp
from kivy.uix.image import Image
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.gridlayout import MDGridLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.slider import MDSlider
from kivymd.icon_definitions import md_icons
from kivy.graphics.texture import Texture
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
import cv2
from enum import Enum
from annotator.annotation_canvas import (AnnotationCanvas)
from annotator.annotation_event import *
from annotation_manager import AnnotationFile
import os
from pprint import pprint


class VideoPlayBackMode(Enum):
    Stopped = 1
    Playing = 2


class VideoAnnotator(MDGridLayout):

    FRAME_COUNT = cv2.CAP_PROP_FRAME_COUNT

    _selected_label = 'smoking'
    annotation_file = None
    annotation_canvas = None
    vid_path = None
    vid_cap = None
    vid_current_frame = 0
    vid_frame_length = 0
    vid_fps = 29
    play_speed = 1
    annotator_fps = 5  # video fps must be divisible by this
    counter = 10
    img = None
    clock = None
    label = 'Smoking'
    dialog = None

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
        self.annotation_canvas.counter = self.counter
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

        self.bottom_layout = MDBoxLayout(
            orientation='horizontal',
            height=dp(40),
            spacing=dp(10),
            padding=[10, 10, 10, 10]
        )
        self.bottom_layout.add_widget(self.time_control_layout)

        self.add_label_button = MDIconButton(
            icon='label',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )

        self.label_text_field = MDTextField(
            hint_text="Enter a new label",
            required=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.6},
            size_hint_x=None,
            width=250
        )

        self.add_label_button.on_press = self.add_label

        self.bottom_layout.add_widget(self.add_label_button)
        self.time_layout.add_widget(self.bottom_layout)
        self.time_control_go_back_button = MDIconButton(
            icon='skip-backward',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )
        self.time_control_go_back_button.on_press = self.on_press_back_button
        self.time_control_layout.add_widget(self.time_control_go_back_button)
        self.time_control_play_button = MDIconButton(
            icon='play',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )
        self.time_control_play_button.on_press = self.on_mouse_down_play_button

        self.time_control_go_next_button = MDIconButton(
            icon='skip-forward',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )
        self.time_control_go_next_button.on_press = self.on_press_next_button
        # self.time_control_play_button.bind(on_touch_down=self.on_mouse_down_play_button)
        self.time_control_layout.add_widget(self.time_control_play_button)
        self.time_control_layout.add_widget(self.time_control_go_next_button)

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
        self.smoking_label = OneLineListItem(
            text='Smoking',
            theme_text_color='Custom',
            text_color='#EEEEEEFF',
            bg_color=(0, 1, 0, .5),
            on_press=self.select_label
        )
        self.label_list.add_widget(self.smoking_label)
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
            self.annotation_file = AnnotationFile(filepath=self.vid_path, img=self.img)
            filename = os.path.splitext(self.vid_path)[0]
            xml_path = os.path.join(self.vid_path, filename + '.xml')
            if os.path.isfile(xml_path):
                # self.annotation_canvas.all_annotations = self.annotation_file.load_pascal_xml_by_filename(xml_path)
                self.annotation_canvas.create_annotation_from_file(self.annotation_file.load_pascal_xml_by_filename(xml_path))
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
                self.check_and_draw_annotation()

    def set_vid_frame_length(self, video_frame):
        self.vid_frame_length = video_frame
        self.time_slider.max = self.convert_video_frame_to_annotator_frame(video_frame)

    def set_vid_current_frame(self, video_frame):
        if self.vid_cap is None or not self.vid_cap.isOpened():
            return False

        has_frames, img = self.vid_cap.read()
        if has_frames:
            self.annotation_canvas.remove_all_annotations()
            buffer = cv2.flip(img, 0).tostring()
            texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
            self.annotation_canvas.texture = texture
            self.vid_current_frame = video_frame
            self.check_and_draw_annotation()
            has_changed_annotator_frame = abs(self.time_slider.value -
                                              self.convert_video_frame_to_annotator_frame(video_frame)) >= 1
            if has_changed_annotator_frame:
                self.time_slider.value = self.convert_video_frame_to_annotator_frame(video_frame)
            return True
        return False

    def play_video(self):
        self.video_playback = VideoPlayBackMode.Playing
        self.time_control_play_button.icon = 'stop'
        self.clock = Clock.schedule_interval(self.playing, 1.0 / self.vid_fps / self.play_speed)

    def playing(self, *args):
        if not self.set_vid_current_frame(self.vid_current_frame+1):
            self.toggle_play()  # To stop playing when video reaches the end

    def stop_video(self):
        self.video_playback = VideoPlayBackMode.Stopped
        self.time_control_play_button.icon = 'play'
        if self.clock is not None:
            self.clock.release()
            self.clock = None

    def stop(self):
        if self.clock is not None:
            self.clock.release()
            self.clock = None
            self.annotation_canvas.remove_all_annotations()

    def on_mouse_down_play_button(self):
        self.toggle_play()

    def toggle_play(self):
        print(self.video_playback)
        if self.video_playback == VideoPlayBackMode.Stopped:
            self.play_video()
        else:
            self.stop_video()

    def convert_video_frame_to_annotator_frame(self, value):
        return int(value / self.vid_fps * self.annotator_fps)

    def convert_video_frame_from_annotator_frame(self, value):
        return int(value * self.vid_fps / self.annotator_fps)

    def on_touch_up_timer_slider(self, widget, touch):
        if self.vid_cap is not None:
            if widget.collide_point(*touch.pos):
                print('touched1')
                # Clock.schedule_once(self.on_timer_slider_update, 0.01)
                print(self.time_slider.value)
                annotation_frame = self.convert_video_frame_from_annotator_frame(self.time_slider.value)
                self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, annotation_frame)
                self.set_vid_current_frame(annotation_frame)

    def on_timer_slider_update(self, widget):
        self.stop_video()
        self.set_vid_current_frame(self.convert_video_frame_from_annotator_frame(self.time_slider.value))

    def on_annotation_canvas_event(self, event):
        # print(event)
        if isinstance(event, AnnotationCreatedEvent):
            # if event.annotation in self.annotation_canvas.annotations:
            #     return
            if not hasattr(event.annotation, 'list_item') or not event.annotation.list_item:
                event.annotation.list_item = OneLineListItem(
                    text=event.annotation.name,
                    theme_text_color='Custom',
                    text_color='#EEEEEEFF'
                )
                self.annotation_list.add_widget(event.annotation.list_item)
        elif isinstance(event, AnnotationDeletedEvent):
            print("removed")
            print(event.annotation)
            if hasattr(event.annotation, 'list_item'):
                self.annotation_list.remove_widget(event.annotation.list_item)
        elif isinstance(event, AnnotationSelectedEvent):
            print('divider color')
            print(event.annotation)
            if hasattr(event.annotation, 'list_item'):
                print(event.annotation.list_item.bg_color)
                for list_item in self.annotation_list.children:
                    if isinstance(list_item, OneLineListItem):
                        list_item.bg_color = (0, 0, 0, 0)
                event.annotation.list_item.bg_color = (0, 1, 0, .5)

    def on_press_next_button(self):
        self.move_annotator_frame_by_delta(1)

    def on_press_back_button(self):
        self.move_annotator_frame_by_delta(-1)

    def move_annotator_frame_by_delta(self, delta_annotator_frame):
        annotator_frame = self.convert_video_frame_to_annotator_frame(self.vid_current_frame) + delta_annotator_frame
        video_frame = self.convert_video_frame_from_annotator_frame(annotator_frame)

        if 0 <= video_frame < self.vid_frame_length:
            self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, video_frame)
            self.set_vid_current_frame(video_frame)

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        print(key)
        print(scancode)
        print(codepoint)
        print(modifier)
        if self.vid_path:
            if key == 32:
                self.toggle_play()
                return
            if self.clock is None:
                if 'ctrl' in modifier and codepoint == 'z':
                    self.annotation_canvas.remove_annotation_at_index(len(self.annotation_canvas.annotations) - 1)
                elif 'ctrl' in modifier and codepoint == 'a':
                    self.annotation_canvas.set_mode_create_annotation(self.label, self.vid_current_frame)
                elif 'ctrl' in modifier and codepoint == 's':
                    self.annotation_file.save_annotations(self.annotation_canvas.all_annotations)
                elif key == 113:
                    self.on_press_back_button()
                elif key == 101:
                    self.on_press_next_button()
                # elif key == 276:
                #     # Left Arrow
                #     self.annotation_canvas.move_left()
                # elif key == 275:
                #     # Right Arrow
                #     self.annotation_canvas.move_right()
                # elif key == 274:
                #     # Down Arrow
                #     self.annotation_canvas.move_down()
                # elif key == 273:
                #     # Up Arrow
                #     self.annotation_canvas.move_up()
                elif key == 127 or key == 8:
                    # Delete Key
                    self.annotation_canvas.remove_selected_annotation()

    def __draw_shadow__(self, origin, end, context=None):
        pass

    def check_and_draw_annotation(self):
        previous_frame = self.vid_current_frame - 1
        if self.vid_current_frame in self.annotation_canvas.all_annotations:
            for annotation in self.annotation_canvas.all_annotations[self.vid_current_frame]:
                annotation.counter = self.counter
                self.annotation_canvas.all_annotations[self.vid_current_frame].append(self.annotation_canvas.create_annotation(annotation, self.vid_current_frame))
                self.annotation_canvas.all_annotations[self.vid_current_frame].remove(annotation)
        # Check if previous frame is labelled
        elif previous_frame in self.annotation_canvas.all_annotations:
            # Iterate through annotations in the frame
            for annotation in self.annotation_canvas.all_annotations[previous_frame]:
                # Check if counter for image is 0, stop displaying
                if annotation.counter > 0:
                    annotation.counter -= 1
                    if self.vid_current_frame in self.annotation_canvas.all_annotations:
                        self.annotation_canvas.all_annotations[self.vid_current_frame].append(self.annotation_canvas.create_annotation(annotation, self.vid_current_frame))
                    else:
                        self.annotation_canvas.all_annotations[self.vid_current_frame] = [self.annotation_canvas.create_annotation(annotation, self.vid_current_frame)]
                    if annotation.counter == 0:
                        self.stop_video()

    def clear_all(self):
        self.annotation_list.clear_widgets()
        self.annotation_canvas.remove_all_annotations()
        self.annotation_canvas.all_annotations = {}

    def add_label(self):
        close_button = MDFlatButton(text='Close', on_release=self.close_dialog)
        confirm_button = MDFlatButton(text="Confirm", on_release=self.confirm_label)
        if self.dialog is None:
            self.dialog = MDDialog(title="Create a new label",
                                   type="custom",
                                   content_cls=self.label_text_field,
                                   buttons=[close_button, confirm_button])
        self.dialog.open()

    def close_dialog(self, obj):
        self.dialog.dismiss()

    def confirm_label(self, obj):
        self.label = self.dialog.content_cls.text
        label = OneLineListItem(
            text=self.label,
            theme_text_color='Custom',
            text_color='#EEEEEEFF',
            bg_color=(0, 0, 0, 0),
            on_press=self.select_label
        )
        self.label_list.add_widget(label)
        self.close_dialog(obj)

    def select_label(self, obj):
        self.label = obj.text
        for list_item in self.label_list.children:
            if isinstance(list_item, OneLineListItem):
                list_item.bg_color = (0, 0, 0, 0)
            obj.bg_color = (0, 1, 0, .5)

