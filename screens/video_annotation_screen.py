from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.gridlayout import MDGridLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.slider import MDSlider
from kivy.graphics.texture import Texture
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.tooltip import MDTooltip
import cv2
import os
from enum import Enum
from kivy.uix.scatterlayout import ScatterLayout
from kivymd.toast import toast
from annotator.annotation_canvas import (AnnotationCanvas)
from annotator.annotation_event import *
from label.annotation_file import AnnotationFile
from object_tracking.annotation_prediction import AnnotationPrediction
from functools import partial


class IconButtonTooltips(MDIconButton, MDTooltip):
    pass


class VideoPlayBackMode(Enum):
    Stopped = 1
    Playing = 2


class VideoAnnotator(MDGridLayout):

    FRAME_COUNT = cv2.CAP_PROP_FRAME_COUNT

    _selected_label = 'smoking'
    annotation_file = None
    annotation_canvas = None
    vid_path = None
    xml_path = None
    vid_cap = None
    vid_current_frame = 0
    vid_frame_length = 0
    vid_fps = 29
    play_speed = 1
    annotator_fps = 5  # video fps must be divisible by this
    prediction_frames = 25
    annotation_per_frame_limit = 3
    counter = 10
    img = None
    clock = None
    label = 'Smoking'
    dialog = None
    label_dialog = None
    object_tracking_mode = True

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        kwargs['md_bg_color'] = (0.141, 0.153, 0.173, 1)
        super(VideoAnnotator, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.on_keyboard, on_resize=self.on_window_resize)  # bind our handler

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
        self.video_annotation_container = MDRelativeLayout()
        self.scatter_canvas = ScatterLayout(do_rotation=False, do_scale=False, do_translation=False)
        self.annotation_canvas = AnnotationCanvas()
        self.scatter_canvas.add_widget(self.annotation_canvas)
        self.video_annotation_container.add_widget(self.scatter_canvas)
        self.main_layout.add_widget(self.video_annotation_container)
        # TODO: Remove this
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
        self.time_slider.bind(on_touch_move=self.on_touch_move_timer_slider, on_touch_down=self.on_touch_down_timer_slider, on_touch_up=self.on_touch_up_timer_slider)
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

        self.toggle_mode_button = IconButtonTooltips(icon='toggle-switch',
                                                     tooltip_text='Toggle to switch off object tracking (ctrl-m)',
                                                     md_bg_color=[.8, .8, .8, 1],
                                                     user_font_size=20)

        self.toggle_mode_button.on_press = self.on_toggle_mode

        self.add_label_button = IconButtonTooltips(icon='label',
                                                   tooltip_text='Add new label (ctrl-l)',
                                                   md_bg_color=[.8, .8, .8, 1],
                                                   user_font_size=20)
        self.add_label_button.on_press = self.add_label

        self.create_annotation_button = IconButtonTooltips(icon='brush',
                                                           tooltip_text='Create new annotation (ctrl-a)',
                                                           md_bg_color=[.8, .8, .8, 1],
                                                           user_font_size=20)

        self.create_annotation_button.on_press = self.on_create_annotation

        self.label_text_field = MDTextField(
            hint_text="Enter a new label",
            required=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.6},
            size_hint_x=None,
            width=250
        )

        self.verify_button = IconButtonTooltips(
            icon='check',
            tooltip_text='Verify all past frames (ctrl-t)',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )

        self.verify_button.on_press = self.on_verify_frame

        self.unverify_button = IconButtonTooltips(
            icon='close',
            tooltip_text='Un-verify all frames (ctrl-u)',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )

        self.unverify_button.on_press = self.on_unverify_frame

        self.save_annotations_button = IconButtonTooltips(
            icon='content-save',
            tooltip_text='Save All Annotations (ctrl-s)',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )

        self.save_annotations_button.on_press = self.on_save_annotations

        self.delete_annotation_button = IconButtonTooltips(
            icon='delete',
            tooltip_text='Delete selected annotation (del)',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )

        self.delete_annotation_button.on_press = self.on_delete_selected_annotation

        self.delete_associated_annotations_button = IconButtonTooltips(
            icon='delete-sweep',
            tooltip_text='Delete all associated annotations based on selected annotation (ctrl-d)',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )

        self.delete_associated_annotations_button.on_press = self.on_remove_all_associated_frames

        self.bottom_features_layout = MDBoxLayout(
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
            padding=[10, 10, 10, 10]
        )

        self.bottom_features_layout.add_widget(self.toggle_mode_button)
        self.bottom_features_layout.add_widget(self.add_label_button)
        self.bottom_features_layout.add_widget(self.create_annotation_button)
        self.bottom_features_layout.add_widget(self.delete_annotation_button)
        self.bottom_features_layout.add_widget(self.delete_associated_annotations_button)
        self.bottom_features_layout.add_widget(self.save_annotations_button)
        self.bottom_features_layout.add_widget(self.verify_button)
        self.bottom_features_layout.add_widget(self.unverify_button)
        self.bottom_layout.add_widget(self.bottom_features_layout)
        self.time_layout.add_widget(self.bottom_layout)
        self.time_control_go_back_button = IconButtonTooltips(
            icon='skip-backward',
            tooltip_text='Go back 5 frames (q or left-arrow)',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )
        self.time_control_go_back_button.on_press = self.on_press_back_button
        self.time_control_layout.add_widget(self.time_control_go_back_button)
        self.time_control_play_button = IconButtonTooltips(
            icon='play',
            tooltip_text='Pause (space-bar)',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        )
        self.time_control_play_button.on_press = self.on_mouse_down_play_button

        self.time_control_go_next_button = IconButtonTooltips(
            icon='skip-forward',
            tooltip_text='Go forward 5 frames (e or right-arrow)',
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

    def on_toggle_mode(self):
        if self.object_tracking_mode:
            self.object_tracking_mode = False
            self.toggle_mode_button.icon = 'toggle-switch-outline'
            self.toggle_mode_button.tooltip_text = "Toggle to switch on object tracking (ctrl-m)"
            toast("Mode switched to Manual")
        else:
            self.object_tracking_mode = True
            self.toggle_mode_button.icon = 'toggle-switch'
            self.toggle_mode_button.tooltip_text = "Toggle to switch off object tracking (ctrl-m)"
            toast("Mode switched to Object Tracking")

    def on_window_resize(self, context, width, height):
        Clock.schedule_once(self.adjust_annotation_size_pos, 0.05)

    def adjust_annotation_size_pos(self, context):
        if self.vid_cap is not None:
            cw, ch = self.video_annotation_container.size
            vw, vh = self.vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

            width_scale = cw / vw
            height_scale = ch / vh

            if width_scale < height_scale:
                scale = width_scale
                center_pos = 0, int((ch - scale * vh) / 2)
            else:
                scale = height_scale
                center_pos = int((cw - scale * vw) / 2), 0

            self.scatter_canvas._set_scale(scale)
            self.scatter_canvas.pos = center_pos

    def load_video(self, video_path):
        # tracemalloc.start()
        self.vid_path = video_path
        self.vid_cap = cv2.VideoCapture(video_path)
        self.vid_current_frame = 0
        self.time_slider.value = 0
        self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.vid_fps = self.vid_cap.get(cv2.CAP_PROP_FPS)
        print('FPS')
        print(self.vid_fps)
        self.set_vid_frame_length(int(self.vid_cap.get(cv2.CAP_PROP_FRAME_COUNT) - 1))
        if self.vid_cap.isOpened():
            has_frames, img = self.vid_cap.read()
            self.annotation_file = AnnotationFile(filepath=self.vid_path, img=img)
            filename = os.path.splitext(self.vid_path)[0]
            self.xml_path = os.path.join(self.vid_path, filename + '.xml')
            if os.path.isfile(self.xml_path):
                # self.annotation_canvas.all_annotations = self.annotation_file.load_pascal_xml_by_filename(xml_path)
                self.annotation_canvas.create_annotation_from_file(self.annotation_file.load_pascal_xml_by_filename(self.xml_path))
            if has_frames:
                buffer = cv2.flip(img, 0).tostring()
                texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
                self.annotation_canvas.texture = texture
                self.annotation_canvas.size_hint_x = None
                self.annotation_canvas.size_hint_y = None
                self.annotation_canvas.width = dp(img.shape[1])
                self.annotation_canvas.height = dp(img.shape[0])
                self.check_and_draw_annotation()
                self.on_window_resize(None, None, None)

                # To fix the scatter_canvas to follow the video screen size so that mouse interaction will work
                self.scatter_canvas.size_hint = None, None
                self.scatter_canvas.size = dp(self.vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH)), dp(self.vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def set_vid_frame_length(self, video_frame):
        self.vid_frame_length = video_frame
        self.time_slider.max = self.convert_video_frame_to_annotator_frame(video_frame)

    def set_vid_current_frame(self, video_frame):
        if self.vid_cap is None or not self.vid_cap.isOpened():
            return False

        has_frames, img = self.vid_cap.read()
        if has_frames:
            buffer = cv2.flip(img, 0).tostring()
            texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
            self.annotation_canvas.texture = texture
            self.vid_current_frame = video_frame
            has_changed_annotator_frame = abs(self.time_slider.value -
                                              self.convert_video_frame_to_annotator_frame(video_frame)) >= 1
            if has_changed_annotator_frame:
                self.check_and_draw_annotation()
                self.time_slider.value = self.convert_video_frame_to_annotator_frame(video_frame)
            return True
        return False

    def play_video(self):
        self.video_playback = VideoPlayBackMode.Playing
        self.time_control_play_button.icon = 'stop'
        self.time_control_play_button.tooltip_text = 'pause (space-bar)'
        if self.clock is not None:
            self.clock.cancel()
        self.clock = Clock.schedule_interval(self.playing, 1.0 / self.vid_fps / self.play_speed)

    def playing(self, *args):
        if not self.set_vid_current_frame(self.vid_current_frame+1):
            self.toggle_play()  # To stop playing when video reaches the end

    def stop_video(self):
        self.video_playback = VideoPlayBackMode.Stopped
        self.time_control_play_button.icon = 'play'
        self.time_control_play_button.tooltip_text = 'play (space-bar)'
        if self.clock is not None:
            self.clock.cancel()
            self.clock = None

    def stop(self):
        if self.clock is not None:
            self.clock.cancel()
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

    def get_annotation_interval(self):
        return self.vid_fps / self.annotator_fps

    def get_current_annotation_frame(self):
        return self.vid_current_frame - (self.vid_current_frame % self.get_annotation_interval())

    def convert_video_frame_to_annotator_frame(self, value):
        return int(value / self.vid_fps * self.annotator_fps)

    def convert_video_frame_from_annotator_frame(self, value):
        return int(value * self.vid_fps / self.annotator_fps)

    def on_touch_move_timer_slider(self, widget, touch):
        if self.vid_cap is not None and widget.collide_point(*touch.pos):
            self.annotation_canvas.remove_all_annotations()
            annotation_frame = self.convert_video_frame_from_annotator_frame(self.time_slider.value)
            self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, annotation_frame)
            self.set_vid_current_frame(annotation_frame)
            self.check_and_draw_annotation()

    def on_touch_down_timer_slider(self, widget, touch):
        if self.vid_cap is not None and widget.collide_point(*touch.pos):
            if self.clock is not None:
                self.stop_video()

    def on_touch_up_timer_slider(self, widget, touch):
        if self.vid_cap is not None and widget.collide_point(*touch.pos):
            self.on_touch_move_timer_slider(widget, touch)
            if self.clock is None:
                self.play_video()

    def on_timer_slider_update(self, widget):
        self.stop_video()
        self.set_vid_current_frame(self.convert_video_frame_from_annotator_frame(self.time_slider.value))

    def on_annotation_canvas_event(self, event: object):
        # print(event)
        if isinstance(event, AnnotationCreatedEvent):
            # if event.annotation in self.annotation_canvas.annotations:
            #     return
            Window.set_system_cursor('arrow')
            if hasattr(event.annotation, 'name'):
                event.annotation.list_item = OneLineListItem(
                    text=event.annotation.name,
                    theme_text_color='Custom',
                    text_color='#EEEEEEFF',
                    on_press=lambda *args: self.set_selected_annotation(event.annotation)
                )
                self.annotation_list.add_widget(event.annotation.list_item)
                # Run Prediction
                if event.is_interactive and self.object_tracking_mode:
                    prediction = AnnotationPrediction()
                    prediction.on_complete_prediction = self.on_complete_prediction
                    if prediction.start(
                        event.annotation,
                        self.vid_path,
                        event.annotation,
                        self.get_current_annotation_frame(),
                        self.get_annotation_interval(),
                        self.prediction_frames,
                        event.annotation.n_id
                    ):
                        toast("Object tracking in progress. Please wait")
                    else:
                        toast("Ensure you have drawn the annotation correctly. Please delete and re-draw the annotation")

        elif isinstance(event, AnnotationDeletedEvent):
            if hasattr(event.annotation, 'list_item'):
                self.annotation_list.remove_widget(event.annotation.list_item)

        elif isinstance(event, AnnotationSelectedEvent):
            if hasattr(event.annotation, 'list_item'):
                print(event.annotation.list_item.bg_color)
                for list_item in self.annotation_list.children:
                    if isinstance(list_item, OneLineListItem):
                        list_item.bg_color = (0, 0, 0, 0)
                event.annotation.list_item.bg_color = (0, 1, 0, .5)

    def set_selected_annotation(self, annotation):
        self.annotation_canvas.select_annotation(annotation)

    def on_complete_prediction(self, context, result, n_id):
        for key, value in result.items():
            key_frame = self.annotation_canvas.all_annotations.setdefault(int(key), [])
            annotation_graphic = AnnotationGraphic(
                parent=self.annotation_canvas,
                name=context.name,
                frame=int(key),
                counter=-1,
                verified=False,
                n_id=n_id,
                bounding_box=(value.min_x, value.min_y, value.max_x, value.max_y),
                color=(0, 1, 0, 1)
            )
            if len(key_frame) < self.annotation_per_frame_limit:
                key_frame.append(annotation_graphic)
        toast('Object Tracking is completed')

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
                # space-bar
                self.toggle_play()
                return
            if self.clock is None:
                if 'ctrl' in modifier and codepoint == 'z':
                    self.annotation_canvas.remove_annotation_at_index(len(self.annotation_canvas.annotations) - 1)
                elif 'ctrl' in modifier and codepoint == 'a':
                    self.on_create_annotation()
                elif 'ctrl' in modifier and codepoint == 's':
                    self.on_save_annotations()
                elif 'ctrl' in modifier and codepoint == 't':
                    self.on_verify_frame()
                elif 'ctrl' in modifier and codepoint == 'd':
                    self.on_remove_all_associated_frames()
                elif 'ctrl' in modifier and codepoint == 'u':
                    self.on_unverify_frame()
                elif 'ctrl' in modifier and codepoint == 'm':
                    self.on_toggle_mode()
                elif 'ctrl' in modifier and codepoint == 'l':
                    self.add_label()
                elif key == 113 or key == 276:
                    # Q or Left Arrow
                    self.on_press_back_button()
                elif key == 101 or key == 275:
                    # E or Right Arrow
                    self.on_press_next_button()
                elif key == 127 or key == 8:
                    # Delete Key
                    self.on_delete_selected_annotation()

    def __draw_shadow__(self, origin, end, context=None):
        pass

    def check_and_draw_annotation(self):
        self.annotation_list.clear_widgets()
        self.annotation_canvas.remove_all_annotations()
        current_frame = self.vid_current_frame - (self.vid_current_frame % self.get_annotation_interval())
        previous_frame = current_frame - self.get_annotation_interval()

        # Redraw current frame annotations
        if current_frame in self.annotation_canvas.all_annotations:
            for annotation in self.annotation_canvas.all_annotations[current_frame]:
                self.annotation_canvas.create_annotation_graphics(annotation, current_frame)

        # Check if previous frame is labelled
        if not self.object_tracking_mode and previous_frame in self.annotation_canvas.all_annotations:
            # Iterate through annotations in the frame
            for annotation in self.annotation_canvas.all_annotations[previous_frame]:
                # Check if counter for image is 0, stop displaying

                if annotation.counter > 0:
                    if annotation.counter == 1:
                        self.stop_video()
                        toast("Video paused, adjust or click on annotation for it to continue annotating")
                    annotation.counter -= 1
                    key_frame = self.annotation_canvas.all_annotations.setdefault(int(current_frame), [])
                    if len(key_frame) < self.annotation_per_frame_limit:
                        key_frame.append(self.annotation_canvas.create_annotation(annotation, current_frame))
                        previous_annotation_index = self.annotation_canvas.all_annotations[previous_frame].index(annotation)
                        self.annotation_canvas.all_annotations[previous_frame][previous_annotation_index].counter = -1
                elif annotation.counter != -1:
                    previous_annotation_index = self.annotation_canvas.all_annotations[previous_frame].index(annotation)
                    self.annotation_canvas.all_annotations[previous_frame][previous_annotation_index].counter = -1

    def clear_all(self):
        self.annotation_list.clear_widgets()
        self.annotation_canvas.remove_all_annotations()
        self.annotation_canvas.all_annotations.clear()
        if self.clock is not None:
            self.clock.cancel()
        if self.vid_cap is not None:
            self.vid_cap.release()

    def on_save_annotations(self):
        confirm_button = MDFlatButton(text="Okay", on_release=self.close_dialog)
        if self.annotation_file is not None:
            if self.annotation_file.save_annotations(self.annotation_canvas.all_annotations):
                self.dialog = MDDialog(title="All annotated frames are saved",
                                       type="custom",
                                       buttons=[confirm_button])
            else:
                self.dialog = MDDialog(title="All annotated frames are saved",
                                       type="custom",
                                       buttons=[confirm_button])
        self.dialog.open()

    def on_create_annotation(self):
        if self.annotation_canvas.mode == 'create_annotation':
            Window.set_system_cursor('arrow')
            self.annotation_canvas.mode = None
            return
        if len(self.annotation_canvas.annotations) < self.annotation_per_frame_limit:
            Window.set_system_cursor('crosshair')
            rounded_to_annotation_frame = self.annotator_fps * round(self.vid_current_frame / self.annotator_fps)
            Clock.schedule_once(partial(self.annotation_canvas.set_mode_create_annotation, label_name=self.label, frame=rounded_to_annotation_frame), 0.1)
        else:
            toast("Only maximum of two annotations can be made")

    def add_label(self):
        close_button = MDFlatButton(text='Close', on_release=self.close_label_dialog)
        confirm_button = MDFlatButton(text="Confirm", on_release=self.confirm_label)
        if self.label_dialog is None:
            self.label_dialog = MDDialog(title="Create a new label",
                                         type="custom",
                                         content_cls=self.label_text_field,
                                         buttons=[close_button, confirm_button])
        self.label_dialog.open()

    def close_dialog(self, obj):
        self.dialog.dismiss()
        self.dialog = None

    def close_label_dialog(self, obj):
        self.label_dialog.dismiss()

    def confirm_label(self, obj):
        self.label = self.label_dialog.content_cls.text
        label = OneLineListItem(
            text=self.label,
            theme_text_color='Custom',
            text_color='#EEEEEEFF',
            bg_color=(0, 0, 0, 0),
            on_press=self.select_label
        )
        self.label_list.add_widget(label)
        self.close_label_dialog(obj)

    def select_label(self, obj):
        self.label = obj.text
        for list_item in self.label_list.children:
            if isinstance(list_item, OneLineListItem):
                list_item.bg_color = (0, 0, 0, 0)
            obj.bg_color = (0, 1, 0, .5)

    def on_verify_frame(self):
        confirm_button = MDFlatButton(text="Okay", on_release=self.close_dialog)
        if self.annotation_file is not None:
            self.annotation_file.save_annotations(self.annotation_canvas.all_annotations)
            if self.annotation_file.verify_till_frame(self.vid_current_frame):
                self.annotation_canvas.create_annotation_from_file(
                    self.annotation_file.load_pascal_xml_by_filename(self.xml_path))
                self.check_and_draw_annotation()
                self.dialog = MDDialog(title="All frames before current frame are verified",
                                       type="custom",
                                       buttons=[confirm_button])
            else:
                self.dialog = MDDialog(title="Error has occurred, check if any annotations are saved",
                                       type="custom",
                                       buttons=[confirm_button])
        self.dialog.open()

    def on_unverify_frame(self):
        confirm_button = MDFlatButton(text="Okay", on_release=self.close_dialog)
        if self.annotation_file is not None:
            self.annotation_file.save_annotations(self.annotation_canvas.all_annotations)
            if self.annotation_file.unverify_all():
                self.annotation_canvas.create_annotation_from_file(
                    self.annotation_file.load_pascal_xml_by_filename(self.xml_path))
                self.check_and_draw_annotation()
                self.dialog = MDDialog(title="All frames are now unverified",
                                       type="custom",
                                       buttons=[confirm_button])
            else:
                self.dialog = MDDialog(title="Error has occurred, check if u have saved the annotations",
                                       type="custom",
                                       buttons=[confirm_button])
        self.dialog.open()

    def on_remove_all_associated_frames(self):
        # confirm_button = MDFlatButton(text="Okay", on_release=self.close_dialog)
        if self.annotation_canvas.remove_associated_frames():
            toast("All associated frames to the selected frame has been removed",)
            # self.dialog = MDDialog(title="All associated frames to the selected frame has been removed",
            #                        type="custom",
            #                        buttons=[confirm_button])
        else:
            # self.dialog = MDDialog(title="Please ensure you have selected the annotation by clicking on it",
            #                        type="custom",
            #                        buttons=[confirm_button])
            toast("Please ensure you have selected the annotation by clicking on it")
        # self.dialog.open()

    def on_delete_selected_annotation(self):
        if self.annotation_canvas.remove_selected_annotation():
            toast("Selected annotation has been removed")
        else:
            toast("No annotation has been selected, please select before deleting")
