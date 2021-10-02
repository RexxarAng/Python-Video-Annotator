import sys
import os
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs


class PascalVocWriter:
    def _read_(self,folder_name,filename,img_size,database_src='unknown', local_img_path=None):
        self.folder_name = folder_name
        self.filename = filename
        self.database_src = database_src
        self.img_size = img_size
        self.box_list = []
        self.local_img_path = local_img_path
        self.verified = False



    #return XML root
    def _xml(self):
        if self.filename is None or \
            self.folder_name is None or \
            self.img_size is None:
            return None

        top = Element('annotation')
        if self.verified:
            top.set('verified', 'yes')

        folder = SubElement(top, ' folder')
        folder.text = self.folder_name

        filename = SubElement(top, 'path')
        filename.text = self.filename

        if self.local_img_path is not None:
            local_img_path = SubElement(top, 'path')
            local_img_path.text = self.local_img_path

        source = SubElement(top, 'source')
        database = SubElement(source, 'database')
        database.text = self.database_src

        sizing = SubElement(top,"size")
        width = SubElement(sizing, 'width')
        height = SubElement(sizing, 'height')
        depth = SubElement(sizing, 'depth')
        width.text = str(self.img_size[1])
        height.text = str(self.img_size[0])
        if len(self.img_size) == 3:
            depth.text = str(self.img_size[2])
        else:
            depth.text ='1'

        segmented = SubElement(top, 'segmented')
        segmented.text = '0'

        return top


    def adding_box(self, x_min, y_min, x_max, y_max, name, difficult):
        bnd_box = {'xmin' : x_min, 'ymin': y_min, 'xmax': x_max, 'ymax': y_max}
        bnd_box['name'] = name
        bnd_box['difficult'] = difficult
        self.box_list.append(bnd_box)



    def append(self, top):
        for each_object in self.box_list:
            object_item = SubElement(top, 'object')
            name = SubElement(object_item, 'name')
            name.text = str(each_object['name'])
            pose = SubElement(object_item, 'pose')
            pose.text = "Unspecified"
            truncated = SubElement(object_item, 'truncated')
            # ymax == height or min
            if int(float(each_object['ymax'])) == int(float(self.img_size[0])) or (int(float(each_object['ymin'])) == 1 ):
                truncated.text = '1' 
            # xmax == width or min
            elif (int(float(each_object['xmax'])) == int(float(self.img_size[1]))) or (int(float(each_object['xmin'])) == 1):
                truncated.text = '1'    
            else:
                truncated.text = '0'

        difficult = SubElement(object_item, 'difficult')
        difficult.text = str(bool(each_object['difficult']) & 1)
        bnd_box = SubElement(object_item, 'bndbox')
        x_min = SubElement(bnd_box, 'xmin')
        x_min.text = str(each_object['xmin'])
        y_min = SubElement(bnd_box, 'ymin')
        y_min.text = str(each_object['ymin'])
        x_max = SubElement(bnd_box, 'xmax')
        x_max.text = str(each_object['xmax'])
        y_max = SubElement(bnd_box, 'ymax')
        y_max.text = str(each_object['ymax'])





