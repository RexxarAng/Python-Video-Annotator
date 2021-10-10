from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.core.window import Window
from kivymd.uix.list import OneLineListItem

from annotator.annotation_canvas import (AnnotationCreatedEvent, AnnotationDeletedEvent, AnnotationSelectedEvent)


class CanvasApp(MDApp):
    annotation_canvas = None

    _selected_label = 'smoking'

    def __init__(self, **kwargs):
        super(CanvasApp, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.on_keyboard)  # bind our handler

    def build(self):
        builder = Builder.load_file("test_annotation_canvas.kv")
        return builder

    def on_start(self):
        print('HERE')
        self.root.ids.annotation_canvas.subscribe_event(self.on_annotation_canvas_event)

    def on_annotation_canvas_event(self, event):
        # print(event)
        if isinstance(event, AnnotationCreatedEvent):
            event.annotation.list_item = OneLineListItem(text=event.annotation.name)
            self.root.ids.annotation_list.add_widget(event.annotation.list_item)
        elif isinstance(event, AnnotationDeletedEvent):
            self.root.ids.annotation_list.remove_widget(event.annotation.list_item)
        elif isinstance(event, AnnotationSelectedEvent):
            print('divider color')
            print(event.annotation.list_item.bg_color)
            for list_item in self.root.ids.annotation_list.children:
                if isinstance(list_item, OneLineListItem):
                    list_item.bg_color = (0, 0, 0, 0)
            event.annotation.list_item.bg_color = (0, 1, 0, 1)

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        print(key)
        print(scancode)
        print(codepoint)
        print(modifier)

        if 'ctrl' in modifier and codepoint == 'z':
            self.root.ids.annotation_canvas.remove_annotation_at_index(len(self.annotation_canvas.annotations) - 1)
        elif 'ctrl' in modifier and codepoint == 'a':
            self.root.ids.annotation_canvas.set_mode_create_annotation('smoking1')
        elif key == 276:
            # Left Arrow
            self.root.ids.annotation_canvas.move_left()
        elif key == 275:
            # Right Arrow
            self.root.ids.annotation_canvas.move_right()
        elif key == 274:
            # Down Arrow
            self.root.ids.annotation_canvas.move_down()
        elif key == 273:
            # Up Arrow
            self.root.ids.annotation_canvas.move_up()
        elif key == 127 or key == 8:
            # Delete Key
            self.root.ids.annotation_canvas.remove_selected_annotation()


CanvasApp().run()
