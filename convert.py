import os
import shutil
from PIL import Image
from pymongo import MongoClient


##################
# For now:
#   0 = Ford
#   1 = Chevy
#   2 = Volkswagen
##################

class Converter:
    def __init__(self, in_path, out_path, perc):
        self.in_path = in_path
        self.out_path = out_path
        self.perc_test = perc

    @staticmethod
    def calc(size, box):
        dw = 1. / size[0]
        dh = 1. / size[1]
        x = (box[0] + box[1]) / 2.0
        y = (box[2] + box[3]) / 2.0
        w = box[1] - box[0]
        h = box[3] - box[2]
        x = x * dw
        w = w * dw
        y = y * dh
        h = h * dh
        return x, y, w, h

    @staticmethod
    def get_catnum(c):
        if c == "ford":
            return 0
        elif c == "chevy":
            return 1
        elif c == "volkswagen":
            return 2

    def convert(self):
        client = MongoClient()
        db = client["deep_learning"]

        idx = 1
        file_idx = 1
        # file_percent = 1
        for c in db.collection_names():
            print("coll " + str(idx) + ": " + str(c))
            coll = db[c]
            for entry in coll.find():
                im_name = entry["name"]
                for sub in entry:
                    if sub == "_id" or sub == "name":
                        pass
                    else:
                        xmin = entry[str(sub)]["left x"]
                        xmax = entry[str(sub)]["top y"]
                        ymin = entry[str(sub)]["right x"]
                        ymax = entry[str(sub)]["bottom y"]

                        im_path = os.path.join(self.in_path, im_name)
                        print("im_path: " + im_path)
                        try:
                            im = Image.open(im_path)

                            w = int(im.size[0])
                            h = int(im.size[1])
                            b = (float(xmin), float(xmax), float(ymin), float(ymax))
                            bb = self.calc((w, h), b)
                            cat = self.get_catnum(c)
                            out = self.out_path + "/" + c + "/"
                            shutil.copyfile(im_path, out + im_name)
                            name, ext = os.path.splitext(im_name)
                            file = open(out + name + ".txt", "w")
                            file.write(str(0) + " " + " ".join([str(a) for a in bb]) + "\n")
                            print("File " + str(file_idx).zfill(5) + ": " + im_name)
                            '''if file_percent == self.perc_test:
                                file_percent = 1
                                file.write()'''
                            file_idx += 1

                        except FileNotFoundError:
                            print("[INFO] One of the files listed in the db could not be found"
                                  "     in the given directory! Skipping...")
                            print()

            idx += 1
        print("[INFO] Converted!")
        print()
