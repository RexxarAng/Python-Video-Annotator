from enum import Enum
from abc import ABC, abstractmethod

from kivy.uix.widget import Widget
from kivy.graphics.instructions import Canvas
from kivy.core.text import Label as CoreLabel
from kivy.graphics.vertex_instructions import (Line, Rectangle)
from kivy.graphics.context_instructions import Color
from nanoid import generate


class Corner(Enum):
    Top_Left = 0
    Top_Right = 1
    Bottom_Right = 2
    Bottom_Left = 3


class BoundingBox:
    min_x, min_y = 0, 0
    max_x, max_y = 0, 0

    def __init__(self, **kwargs):
        self.min_x, self.min_y, self.max_x, self.max_y = kwargs['bounding_box']

    def hit(self, x, y):
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def get_size(self):
        return self.max_x - self.min_x, self.max_y - self.min_y

    def get_corner_point(self, corner: Corner):
        if corner == Corner.Top_Left:
            return self.min_x, self.max_y
        if corner == Corner.Top_Right:
            return self.max_x, self.max_y
        if corner == Corner.Bottom_Right:
            return self.max_x, self.min_y
        if corner == Corner.Bottom_Left:
            return self.min_x, self.min_y
        raise NotImplementedError

    def reset_min_max(self):
        # Flip min, max if min is greater then max
        if self.min_x > self.max_x:
            self.min_x, self.max_x = self.max_x, self.min_x
        if self.min_y > self.max_y:
            self.min_y, self.max_y = self.max_y, self.min_y


class CanvasGraphic(ABC):

    def __init__(self):
        self.name = None

    @abstractmethod
    def change_color(self, color): raise NotImplementedError

    @abstractmethod
    def redraw(self): raise NotImplementedError

    @abstractmethod
    def remove_graphic(self): raise NotImplementedError


class IDraggable(ABC):

    @abstractmethod
    def can_drag(self): raise NotImplementedError

    @abstractmethod
    def drag_delta(self, delta_x, delta_y): raise NotImplementedError


class IResizable(ABC):

    @abstractmethod
    def can_resize_corner(self, corner: Corner): raise NotImplementedError

    @abstractmethod
    def resize_corner(self, corner: Corner, x, y): raise NotImplementedError

    @abstractmethod
    def check_hit_resize_corner(self, x, y): raise NotImplementedError


class AnnotationGraphic(BoundingBox, CanvasGraphic, IDraggable, IResizable):

    _border_box = None          # Kivy's Line with 4 points forming rectangle
    _resize_boxes = None        # Kivy's Rectangles
    _label = None               # Kivy's Rectangle with text texture
    _show_resize_hint = False

    def __init__(self, **kwargs):
        # Required parameters
        self.parent = kwargs.get('parent')
        if not isinstance(self.parent, Widget):
            raise ValueError('parent attribute of (kivy.uix.widget) is required')

        self.name = kwargs.get('name', '<no-value>')
        self.frame = kwargs.get('frame', '<no-value>')
        self.color = kwargs.get('color', (0, 1, 0, 0.8))
        self.counter = kwargs.get('counter', '<no-value>')

        super().__init__(**kwargs)

    def redraw(self):
        self._redraw_border_box()
        if self._show_resize_hint is True:
            self._redraw_resize_hint()
        self._redraw_label()

    def _redraw_border_box(self):
        points = ()
        for i in range(0, 4, 1):
            points += self.get_corner_point(Corner(i))

        with self.parent.canvas:
            Color(*self.color)
            if self._border_box is None:
                self._border_box = Line(points=points, close=True, width=1)
            else:
                self._border_box.points = points

    def _redraw_resize_hint(self):
        if self._show_resize_hint:
            with self.parent.canvas:
                # Draw resize-hint-box
                Color(0, 1, 0, 0.5)
                if self._resize_boxes is None:
                    self._resize_boxes = []
                    for _ in range(0, 4, 1):
                        self._resize_boxes.append(Rectangle(pos=(0, 0), size=(20, 20)))

                for index, resize_box in enumerate(self._resize_boxes):
                    point = self.get_corner_point(Corner(index))
                    resize_box.pos = (point[0] - 10, point[1] - 10)
        else:
            if self._resize_boxes:
                for resize_box in self._resize_boxes:
                    self.parent.canvas.remove(resize_box)
                self._resize_boxes = None

    def _redraw_label(self):
        with self.parent.canvas:
            pos = self.get_corner_point(Corner.Top_Left)
            if self._label is None:
                Color(0, 1, 0, 1)
                text_label = CoreLabel(text=self.name, font_size=20)
                text_label.refresh()
                text_texture = text_label.texture

                self._label = Rectangle(
                    pos=pos,
                    size=text_texture.size,
                    texture=text_texture
                )
            else:
                self._label.pos = pos

    def can_drag(self):
        return True

    def drag_delta(self, delta_x, delta_y):
        self.min_x += delta_x
        self.min_y += delta_y
        self.max_x += delta_x
        self.max_y += delta_y
        self.redraw()

    def can_resize_corner(self, corner: Corner):
        return True

    def resize_corner(self, corner: Corner, x, y):
        if corner == Corner.Top_Left:
            self.min_x = x
            self.max_y = y
        elif corner == Corner.Top_Right:
            self.max_x = x
            self.max_y = y
        elif corner == Corner.Bottom_Left:
            self.min_x = x
            self.min_y = y
        elif corner == Corner.Bottom_Right:
            self.max_x = x
            self.min_y = y

    def check_hit_resize_corner(self, x, y):
        # TODO: Clean up this
        if self.min_x - 15 <= x <= self.min_x + 15:
            if self.min_y - 15 <= y <= self.min_y + 15:
                return Corner.Bottom_Left
            if self.max_y - 15 <= y <= self.max_y + 15:
                return Corner.Top_Left
        if self.max_x - 15 <= x <= self.max_x + 15:
            if self.min_y - 15 <= y <= self.min_y + 15:
                return Corner.Bottom_Right
            if self.max_y - 15 <= y <= self.max_y + 15:
                return Corner.Top_Right
        return None

    def change_color(self, color):
        self.color = color
        self.parent.canvas.remove(self._border_box)
        self._border_box = None
        self.redraw()

    def display_resize_hint(self, show):
        self._show_resize_hint = show
        self._redraw_resize_hint()

    def remove_graphic(self):
        self.display_resize_hint(False)
        self.parent.canvas.remove(self._border_box)
        self.parent.canvas.remove(self._label)

