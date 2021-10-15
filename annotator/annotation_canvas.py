from kivy.config import Config
from kivy.uix.image import Image
from kivymd.uix.floatlayout import MDFloatLayout
from pprint import pprint
from annotator.annotation_component import BoundingBox, AnnotationGraphic, Corner, IDraggable
from annotator.annotation_event import *

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')


class AnnotationCanvas(Image):
    mode = None
    MODE_CREATE_ANNOTATION = 'create_annotation'
    MODE_DRAG_ANNOTATION = 'drag_annotation'
    frame = None
    verified = False
    current_label = 'no-label'
    resize_corner: Corner = Corner.Bottom_Right
    all_annotations = {}
    annotations = []
    selected_annotation = None
    initial_mouse_down_pos = None
    previous_mouse_pos = None

    _event_subscribers = []

    def __init__(self, **kwargs):
        super(AnnotationCanvas, self).__init__(**kwargs)

    def subscribe_event(self, fn):
        self._event_subscribers.append(fn)

    def post_event(self, event):
        for event_subscribers in self._event_subscribers:
            event_subscribers(event)

    def update_size(self, instance, size):
        self.g1.redraw()
        print(size)

    def on_touch_down(self, touch):
        print(touch)
        self.initial_mouse_down_pos = (touch.x, touch.y)
        with self.canvas:
            if self.mode is None:
                if self.selected_annotation:
                    _resize_corner = self.selected_annotation.check_hit_resize_corner(touch.x, touch.y)
                    if _resize_corner:
                        self.mode = self.MODE_CREATE_ANNOTATION
                        self.resize_corner = _resize_corner
                        return
                for annotation in self.annotations:
                    if (isinstance(annotation, IDraggable) and annotation.can_drag()
                            and isinstance(annotation, BoundingBox) and annotation.hit(touch.x, touch.y)):
                        if self.selected_annotation is not None:
                            self.selected_annotation.display_resize_hint(False)
                            self.selected_annotation.change_color((0, 1, 0, 0.7))
                        self.mode = self.MODE_DRAG_ANNOTATION
                        self.selected_annotation = annotation
                        self.selected_annotation.display_resize_hint(True)
                        self.selected_annotation.change_color((0, 1, 0, 1))
                        break
            elif self.mode == self.MODE_CREATE_ANNOTATION:
                if self.selected_annotation is not None:
                    self.selected_annotation.display_resize_hint(False)
                    self.selected_annotation.change_color((0, 1, 0, 0.7))
                self.selected_annotation = AnnotationGraphic(
                    parent=self,
                    name=self.current_label,
                    frame=self.frame,
                    bounding_box=(touch.x, touch.y, touch.x, touch.y),
                    color=(0, 1, 0, 1)
                )
                self.selected_annotation.display_resize_hint(True)
                self.selected_annotation.redraw()
                self.annotations.append(self.selected_annotation)
                if self.frame in self.all_annotations:
                    self.all_annotations[self.frame].append(self.convert_annotation_graphic_to_annotation(self.selected_annotation))
                    # self.all_annotations[self.frame].append(self.selected_annotation)
                else:
                    self.all_annotations[self.frame] = [self.convert_annotation_graphic_to_annotation(self.selected_annotation)]
                    # self.all_annotations[self.frame].append(self.selected_annotation)
                self.resize_corner = Corner.Bottom_Right

    def on_touch_move(self, touch):
        with self.canvas:
            if self.mode == self.MODE_CREATE_ANNOTATION and self.selected_annotation:
                self.selected_annotation.resize_corner(self.resize_corner, touch.x, touch.y)
                self.selected_annotation.redraw()
            elif self.mode == self.MODE_DRAG_ANNOTATION and self.selected_annotation:
                if self.previous_mouse_pos:
                    _previous_mouse_pos = self.previous_mouse_pos
                else:
                    _previous_mouse_pos = self.initial_mouse_down_pos
                delta_x = -(_previous_mouse_pos[0] - touch.x)
                delta_y = -(_previous_mouse_pos[1] - touch.y)

                self.selected_annotation.drag_delta(delta_x, delta_y)

        self.previous_mouse_pos = (touch.x, touch.y)

    def on_touch_up(self, touch):
        print('released mouse', touch)
        print(self.annotations)

        if self.selected_annotation:
            self.selected_annotation.reset_min_max()
            self.selected_annotation.redraw()

        if self.mode == self.MODE_CREATE_ANNOTATION:
            self.post_event(AnnotationCreatedEvent(annotation=self.selected_annotation))
            self.mode = None
        elif self.mode == self.MODE_DRAG_ANNOTATION:
            self.post_event(AnnotationUpdatedEvent(annotation=self.selected_annotation))
            self.mode = None

        if self.selected_annotation:
            self.post_event(AnnotationSelectedEvent(annotation=self.selected_annotation))

        self.initial_mouse_down_pos = None
        self.previous_mouse_pos = None

    def set_mode_create_annotation(self, label_name, frame):
        self.frame = frame
        self.mode = self.MODE_CREATE_ANNOTATION
        self.current_label = label_name

    def remove_annotation_at_index(self, index):
        if index >= len(self.annotations) or index < 0:
            print('cannot remove')
            return

        annotation_to_remove = self.annotations[index]
        # self.all_annotations[self.frame].remove(self.annotations[index].)
        self.remove_annotation(annotation_to_remove)

    def remove_selected_annotation(self):
        if self.selected_annotation:
            self.remove_annotation(self.selected_annotation)

    def remove_annotation(self, annotation):
        if annotation:
            annotation.remove_graphic()
            self.annotations.remove(annotation)
            self.post_event(AnnotationDeletedEvent(annotation=annotation))

            if annotation == self.selected_annotation:
                self.selected_annotation = None

    def remove_all_annotations(self):
        for annotation in self.annotations:
            print('actual removing')
            print(annotation)
            self.remove_annotation(annotation)

    def create_annotation(self, annotation):
        annotation_graphic = AnnotationGraphic(
            parent=self,
            name=annotation[0],
            frame=self.frame,
            bounding_box=(annotation[1][0], annotation[1][1], annotation[1][2], annotation[1][3]),
            color=(0, 1, 0, 1)
        )
        annotation_graphic.redraw()
        self.post_event(AnnotationCreatedEvent(annotation=annotation_graphic))
        self.annotations.append(annotation_graphic)

    @staticmethod
    def convert_annotation_graphic_to_annotation(annotation):
        bbox = [annotation.min_x, annotation.min_y, annotation.max_x, annotation.max_y]
        label = annotation.name
        converted_annotation = [label, bbox, False]
        print(converted_annotation)
        return converted_annotation
