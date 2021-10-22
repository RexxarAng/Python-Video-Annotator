import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'label'))
from label.pascal_voc_io import PascalVocReader


class BoundingBox:
    left = 0.0
    bottom = 0.0
    right = 0.0
    top = 0.0

    def return_bounding_box(self):
        return self.left, self.bottom, self.right, self.top

    def check_hit(self, target):
        return not (self.left > target.right
                    or self.right < target.left
                    or self.top < target.bottom
                    or self.bottom > target.top)


def calculate_score(value1: list, value2: list):
    # Check label
    bounding_box1 = BoundingBox()
    bounding_box2 = BoundingBox()
    if value1[0][0] == value2[0][0]:
        bounding_box1.left, bounding_box1.bottom, bounding_box1.right, bounding_box1.top = value1[0][1]
        bounding_box2.left, bounding_box2.bottom, bounding_box2.right, bounding_box2.top = value2[0][1]
        return 1 if bounding_box1.check_hit(bounding_box2) else 0
    else:
        return 0


if len(sys.argv) == 3:
    if os.path.isfile(sys.argv[1]) and os.path.isfile(sys.argv[2]):
        t_voc_parse_reader1 = PascalVocReader(sys.argv[1])
        dict1 = t_voc_parse_reader1.get_annotations()
        t_voc_parse_reader2 = PascalVocReader(sys.argv[2])
        dict2 = t_voc_parse_reader2.get_annotations()

        score = 0
        counter = 0

        d1_iter = iter(dict1)
        d2_iter = iter(dict2)

        i = next(d1_iter, None)
        j = next(d2_iter, None)
        while i is not None or j is not None:
            if i is None:
                counter += 1
                j = next(d2_iter, None)
            elif j is None:
                counter += 1
                i = next(d1_iter, None)
            elif i < j:
                counter += 1
                i = next(d1_iter, None)
            elif i > j:
                counter += 1
                j = next(d2_iter, None)
            else:
                score += calculate_score(dict1[i], dict2[j])
                counter += 1
                i = next(d1_iter, None)
                j = next(d2_iter, None)

        print("First file has a total of", len(dict1), "annotations")
        print("Second file has a total of", len(dict2), "annotations")
        print("Interannotator agreement score:", score / counter)
    else:
        print("Invalid file")
        exit()

else:
    print(sys.argv[1], " ", sys.argv[2])
    print("Invalid arguments")
    exit()
