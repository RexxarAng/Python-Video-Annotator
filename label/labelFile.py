from label.pascal_voc_io import PascalVocWriter, XML_EXT
from enum import Enum
import os.path


class LabelFileFormat(Enum):
    PASCAL_VOC = 1
    YOLO = 2
    CREATE_ML = 3


class LabelFileError(Exception):
    pass


class LabelFile(object):
    # It might be changed as window creates. By default, using XML ext
    # suffix = '.lif'
    suffix = XML_EXT

    def __init__(self, filename=None):
        self.shapes = ()
        self.image_path = None
        self.image_data = None
        self.verified = False

    def save_pascal_voc_format(self, filename, annotations, video_path, image_shape, line_color=None, fill_color=None,
                               database_src=None):
        filename += ".xml"
        video_folder_path = os.path.dirname(video_path)
        video_folder_name = os.path.split(video_folder_path)[-1]
        video_file_name = os.path.basename(video_path)
        writer = PascalVocWriter(video_folder_name, video_file_name,
                                 image_shape, local_img_path=video_path)
        writer.verified = self.verified
        difficult = False
        for frame in annotations:
            frame_object = []
            for annotation in annotations[frame]:
                label = annotation[0]
                bnd_box = LabelFile.convert_cv2_bnd_box_to_points(annotation[1])
                frame_object.append([bnd_box, label, frame])
            writer.add_bnd_box_frame(frame_object)

        writer.save(target_file=filename)
        return

    def toggle_verify(self):
        self.verified = not self.verified

    ''' ttf is disable
    def load(self, filename):
        import json
        with open(filename, 'rb') as f:
                data = json.load(f)
                imagePath = data['imagePath']
                imageData = b64decode(data['imageData'])
                lineColor = data['lineColor']
                fillColor = data['fillColor']
                shapes = ((s['label'], s['points'], s['line_color'], s['fill_color'])\
                        for s in data['shapes'])
                # Only replace data after everything is loaded.
                self.shapes = shapes
                self.imagePath = imagePath
                self.imageData = imageData
                self.lineColor = lineColor
                self.fillColor = fillColor

    def save(self, filename, shapes, imagePath, imageData, lineColor=None, fillColor=None):
        import json
        with open(filename, 'wb') as f:
                json.dump(dict(
                    shapes=shapes,
                    lineColor=lineColor, fillColor=fillColor,
                    imagePath=imagePath,
                    imageData=b64encode(imageData)),
                    f, ensure_ascii=True, indent=2)
    '''

    @staticmethod
    def is_label_file(filename):
        file_suffix = os.path.splitext(filename)[1].lower()
        return file_suffix == LabelFile.suffix

    @staticmethod
    def convert_points_to_bnd_box(points):
        x_min = float('inf')
        y_min = float('inf')
        x_max = float('-inf')
        y_max = float('-inf')
        for p in points:
            x = p[0]
            y = p[1]
            x_min = min(x, x_min)
            y_min = min(y, y_min)
            x_max = max(x, x_max)
            y_max = max(y, y_max)

        # Martin Kersner, 2015/11/12
        # 0-valued coordinates of BB caused an error while
        # training faster-rcnn object detector.
        if x_min < 1:
            x_min = 1

        if y_min < 1:
            y_min = 1

        return int(x_min), int(y_min), int(x_max), int(y_max)



    @staticmethod
    def convert_cv2_bnd_box_to_points(bnd_box):
        x_min = bnd_box[0]
        y_min = bnd_box[1]
        x_max = x_min + bnd_box[2]
        y_max = y_min + bnd_box[3]

        return int(x_min), int(y_min), int(x_max), int(y_max)
