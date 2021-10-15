from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs

XML_EXT = '.xml'
ENCODE_METHOD = 'utf-8'
DEFAULT_ENCODING = 'utf-8'


class PascalVocWriter:

    def __init__(self, folder_name, filename, img_size, database_src='Unknown', local_vid_path=None):
        self.folder_name = folder_name
        self.filename = filename
        self.database_src = database_src
        self.img_size = img_size
        self.box_list = []
        self.local_vid_path = local_vid_path

    def prettify(self, elem):
        """
            Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf8')
        print(rough_string)
        root = etree.fromstring(rough_string)
        return etree.tostring(root, pretty_print=True, encoding=ENCODE_METHOD).replace("  ".encode(), "\t".encode())
        # minidom does not support UTF-8
        # reparsed = minidom.parseString(rough_string)
        # return reparsed.toprettyxml(indent="\t", encoding=ENCODE_METHOD)

    def gen_xml(self):
        """
            Return XML root
        """
        # Check conditions
        if self.filename is None or \
                self.folder_name is None or \
                self.img_size is None:
            return None

        top = Element('annotations')
        # if self.verified:
        #     top.set('verified', 'yes')

        folder = SubElement(top, 'folder')
        folder.text = self.folder_name

        filename = SubElement(top, 'filename')
        filename.text = self.filename

        if self.local_vid_path is not None:
            local_img_path = SubElement(top, 'path')
            local_img_path.text = self.local_vid_path

        source = SubElement(top, 'source')
        database = SubElement(source, 'database')
        database.text = self.database_src

        size_part = SubElement(top, 'size')
        width = SubElement(size_part, 'width')
        height = SubElement(size_part, 'height')
        depth = SubElement(size_part, 'depth')
        width.text = str(self.img_size[1])
        height.text = str(self.img_size[0])
        if len(self.img_size) == 3:
            depth.text = str(self.img_size[2])
        else:
            depth.text = '1'

        segmented = SubElement(top, 'segmented')
        segmented.text = '0'
        return top

    def add_bnd_box_frame(self, frame_object):
        frame_array = []
        for frame in frame_object:
            box = frame[0]
            bnd_box = {'xmin': box[0], 'ymin': box[1], 'xmax': box[2], 'ymax': box[3], 'name': frame[1],
                       'frame': frame[2], 'verified': frame[3]}
            frame_array.append(bnd_box)
        self.box_list.append(frame_array)

    def append_objects(self, top, verified=False):
        start_frame = SubElement(top, 'startframe')
        end_frame = SubElement(top, 'endframe')
        main_annotations = SubElement(top, 'frames')
        start_frame.text = str(self.box_list[0][0]['frame'])
        end_frame.text = str(self.box_list[-1][-1]['frame'])
        for frame_array in self.box_list:
            frame_object = SubElement(main_annotations, 'frame')
            if frame_array[0]['verified']:
                frame_object.attrib['verified'] = 'yes'
            frame_number = SubElement(frame_object, "framenumber")
            frame_number.text = str(frame_array[0]['frame'])
            for each_object in frame_array:
                annotation = SubElement(frame_object, 'annotation')
                name = SubElement(annotation, 'name')
                name.text = str(each_object['name'])
                truncated = SubElement(annotation, 'truncated')
                if int(float(each_object['ymax'])) == int(float(self.img_size[0])) or (
                        int(float(each_object['ymin'])) == 1):
                    truncated.text = "1"  # max == height or min
                elif (int(float(each_object['xmax'])) == int(float(self.img_size[1]))) or (
                        int(float(each_object['xmin'])) == 1):
                    truncated.text = "1"  # max == width or min
                else:
                    truncated.text = "0"
                bnd_box = SubElement(annotation, 'bndbox')
                x_min = SubElement(bnd_box, 'xmin')
                x_min.text = str(each_object['xmin'])
                y_min = SubElement(bnd_box, 'ymin')
                y_min.text = str(each_object['ymin'])
                x_max = SubElement(bnd_box, 'xmax')
                x_max.text = str(each_object['xmax'])
                y_max = SubElement(bnd_box, 'ymax')
                y_max.text = str(each_object['ymax'])

    @staticmethod
    def toggle_verify(frame, filename):
        assert filename.endswith(XML_EXT), "Unsupported file format"
        parser = etree.XMLParser(encoding=ENCODE_METHOD)
        et = ElementTree.parse(filename, parser=parser)
        xml_tree = et.getroot()
        for node in xml_tree.findall('.//framenumber'):
            if int(node.text) == frame:
                parent_tag = node.find('..')
                try:
                    verified = parent_tag.attrib['verified']
                    if verified == 'yes':
                        del parent_tag.attrib['verified']
                except KeyError:
                    parent_tag.attrib['verified'] = 'yes'
                    pass
                break
        et.write(filename)

    def save(self, target_file=None):
        root = self.gen_xml()
        self.append_objects(root)
        out_file = None
        if target_file is None:
            out_file = codecs.open(
                self.filename + XML_EXT, 'w', encoding=ENCODE_METHOD)
        else:
            out_file = codecs.open(target_file, 'w', encoding=ENCODE_METHOD)

        prettify_result = self.prettify(root)
        out_file.write(prettify_result.decode('utf8'))
        out_file.close()


class PascalVocReader:

    def __init__(self, file_path, frame=None):
        self.annotations = {}
        self.file_path = file_path
        self.verified = False
        try:
            self.parse_xml()
        except:
            pass

    def get_annotations(self):
        return self.annotations

    @staticmethod
    def convert_points_to_cv2_bnd_box(bnd_box):
        x_min = int(float(bnd_box.find('xmin').text))
        y_min = int(float(bnd_box.find('ymin').text))
        x_max = int(float(bnd_box.find('xmax').text))
        y_max = int(float(bnd_box.find('ymax').text))
        return x_min, y_min, x_max, y_max

    def parse_xml(self):
        assert self.file_path.endswith(XML_EXT), "Unsupported file format"
        parser = etree.XMLParser(encoding=ENCODE_METHOD)
        xml_tree = ElementTree.parse(self.file_path, parser=parser).getroot()
        self.annotations = {}
        frames = xml_tree.find('frames')
        for object_iter in frames.iter('frame'):
            frame_number = int(object_iter.find('framenumber').text)
            try:
                verified = object_iter.attrib['verified']
                if verified == 'yes':
                    self.verified = True
            except KeyError:
                self.verified = False
                pass
            annotations = []
            for annotation_iter in object_iter.iter('annotation'):
                bnd_box = annotation_iter.find('bndbox')
                bnd_box = self.convert_points_to_cv2_bnd_box(bnd_box)
                label = annotation_iter.find('name').text
                annotations.append([label, bnd_box, self.verified])
            self.annotations[frame_number] = annotations
        return True



