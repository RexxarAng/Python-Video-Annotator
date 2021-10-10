from kivy.core.window import Window
from kivy.graphics import Color
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.gridlayout import MDGridLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.slider import MDSlider
from kivymd.icon_definitions import md_icons

from annotator.annotation_canvas import (AnnotationCanvas)
from annotator.annotation_event import *


class VideoAnnotator(MDGridLayout):

    _selected_label = 'smoking'

    annotation_canvas = None

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        kwargs['md_bg_color'] = (0.141, 0.153, 0.173, 1)
        super(VideoAnnotator, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.on_keyboard)  # bind our handler

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
        self.time_control_layout.add_widget(MDIconButton(
            icon='play',
            md_bg_color=[.8, .8, .8, 1],
            user_font_size=20
        ))
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

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        print(key)
        print(scancode)
        print(codepoint)
        print(modifier)

        if 'ctrl' in modifier and codepoint == 'z':
            self.annotation_canvas.remove_annotation_at_index(len(self.annotation_canvas.annotations) - 1)
        elif 'ctrl' in modifier and codepoint == 'a':
            self.annotation_canvas.set_mode_create_annotation('smoking1')
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
