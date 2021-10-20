import collections
import os
from label.pascal_voc_io import PascalVocWriter, PascalVocReader


class AnnotationFile:
    img = None

    def __init__(self, **kwargs):
        self.filepath = kwargs['filepath']
        self.img = kwargs['img']
        self.filename = os.path.splitext(self.filepath)[0]

    def save_annotations(self, annotations):
        print("try saving")
        image_annotations = {}
        print("input")
        print(annotations)
        for frame in annotations:
            for i in annotations[frame]:
                bbox = [i.min_x, i.min_y, i.max_x, i.max_y]
                label = i.name
                annotation = [label, bbox, i.verified]
                if frame in image_annotations:
                    image_annotations[frame].append(annotation)
                else:
                    image_annotations[frame] = [annotation]
        print(image_annotations)
        try:
            filename = self.filename + ".xml"
            video_folder_path = os.path.dirname(self.filepath)
            video_folder_name = os.path.split(video_folder_path)[-1]
            video_file_name = os.path.basename(self.filepath)
            writer = PascalVocWriter(video_folder_name, video_file_name,
                                     self.img.shape, local_vid_path=self.filepath)
            image_annotations = collections.OrderedDict(sorted(image_annotations.items()))
            for frame in image_annotations:
                frame_object = []
                for annotation in image_annotations[frame]:
                    label = annotation[0]
                    bnd_box = annotation[1]
                    verified = annotation[2]
                    frame_object.append([bnd_box, label, frame, verified])
                writer.add_bnd_box_frame(frame_object)
            if annotations:
                writer.save(target_file=filename)
                return True

            return False
            # self.label_file.save_pascal_voc_format(filename=self.filename, annotations=image_annotations,
            #                                        video_path=self.filepath, image_shape=self.img.shape)
        except:
            print("Error!")
            return False

    def load_pascal_xml_by_filename(self, xml_path):
        if self.filepath is None:
            return
        if os.path.isfile(xml_path) is False:
            return

        t_voc_parse_reader = PascalVocReader(xml_path)
        image_annotations = t_voc_parse_reader.get_annotations()
        return image_annotations
        # shapes = t_voc_parse_reader.get_shapes();
        # self.load_labels(shapes)
        # self.canvas.verified = t_voc_parse_reader.verified

    def toggle_verify(self, frame):
        video_folder_path = os.path.dirname(self.filepath)
        video_folder_name = os.path.split(video_folder_path)[-1]
        video_file_name = os.path.basename(self.filepath)

        writer = PascalVocWriter(video_folder_name, video_file_name,
                                 self.img.shape, local_vid_path=self.filepath)
        xml_file = self.filename + '.xml'
        return writer.toggle_verify_till_frame(frame, xml_file)

    def verify_till_frame(self, frame):
        video_folder_path = os.path.dirname(self.filepath)
        video_folder_name = os.path.split(video_folder_path)[-1]
        video_file_name = os.path.basename(self.filepath)

        writer = PascalVocWriter(video_folder_name, video_file_name,
                                 self.img.shape, local_vid_path=self.filepath)
        xml_file = self.filename + '.xml'
        if os.path.isfile(xml_file):
            return writer.verify_till_frame(frame, xml_file)
        else:
            return False

    def unverify_all(self):
        video_folder_path = os.path.dirname(self.filepath)
        video_folder_name = os.path.split(video_folder_path)[-1]
        video_file_name = os.path.basename(self.filepath)

        writer = PascalVocWriter(video_folder_name, video_file_name,
                                 self.img.shape, local_vid_path=self.filepath)
        xml_file = self.filename + '.xml'
        if os.path.isfile(xml_file):
            return writer.unverify_all(xml_file)
        else:
            return False
