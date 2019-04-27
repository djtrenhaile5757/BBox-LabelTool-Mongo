import os
from pymongo import MongoClient
from PIL import Image, ImageTk


class FunctionController:
    def __init__(self, top):
        client = MongoClient()
        self.db = client.deep_learning
        self.skipdir = os.path.join(top, "skipped")

        self.im_paths = []
        self.im_path = ""
        self.im_name = ""
        self.im_idx = -1
        self.total = 0

    def load_dir(self, dir, brand):
        subdir = "/" + brand
        s = dir + "/objects" + subdir
        skip_dir = s + "/skipped" + subdir

        if not os.path.isdir(s):
            print("[INFO] Directory doesn't exist!")
            return

        for _, _, files in os.walk(s):
            for file in files:
                im_path = os.path.join(s, file)
                if file == ".DS_Store":
                    pass
                else:
                    self.im_paths.append(im_path)

        self.total = len(self.im_paths)
        if self.total == 0:
            print("[INFO] Directory is empty!")

        return self.total, s

    def load_image(self):
        self.im_path = self.im_paths[self.im_idx]
        self.im_name = os.path.basename(self.im_path)
        try:
            image = Image.open(self.im_path)
        except:
            print("[INFO] Could not open selected image!")
            return None, None, "repeat"

        size = image.size
        resize_ratio = 850
        r = resize_ratio / size[0]
        dim = (resize_ratio, int(size[1] * r))
        image = image.resize((dim[0], dim[1]), Image.LANCZOS)
        tkimg = ImageTk.PhotoImage(image)

        prev_bboxes = self.gather_previms()
        return tkimg, prev_bboxes, [self.im_idx + 1, self.total]

    def save_image(self, annotations):
        self.purge_old_entries()
        for ann in annotations:
            final_data = {"name": self.im_name}
            brand = ann[0]

            i = 1
            for bbox in ann[1]:
                object = {"left x": str(bbox[0]),
                          "top y": str(bbox[1]),
                          "right x": str(bbox[2]),
                          "bottom y": str(bbox[3])}
                final_data[str(i)] = object
                i += 1

            self.db[brand].insert_one(final_data)
            print("[INFO] Database entry: ")
            print("         " + str(final_data))

    def next_image(self, idx=0):
        if idx is not 0:
            print("idx: " + str(idx))
            self.im_idx = idx - 2
        if self.im_idx + 1 == self.total:
            print("[INFO] At end of image pool!")
            return None, None, "end"
        self.im_idx += 1
        t, b, a = self.load_image()
        return t, b, a

    def prev_image(self, event=None):
        if self.im_idx == 0:
            print("[INFO] Already at beginning of image pool!")
            return
        self.im_idx -= 1
        t, b, a = self.load_image()
        return t, b, a

    def skip_im(self):
        print("moving image: " + self.im_name)
        if not os.path.exists(self.skipdir):
            os.mkdir(self.skipdir)

        skip_path = os.path.join(self.skipdir, os.path.basename(self.im_name))
        os.rename(self.im_path, skip_path)

        self.total -= 1
        self.im_idx -= 1
        for path in self.im_paths:
            if path == self.im_path:
                self.im_paths.remove(path)

    def search_immum(self, idx):
        if 1 <= idx <= self.total:
            self.im_idx = idx
            self.load_image()

    def gather_previms(self):
        matching_ims = []
        for coll in self.db.collection_names():
            data = self.db[coll].find_one({"name": self.im_name})
            if data is not None:
                entry = [data, coll]
                matching_ims.insert(0, entry)   # counteracts the 'reverse searching' of mongo

        for match in matching_ims:
            data = match[0]
            bboxes = []
            i = 1
            while i < len(data.keys()) - 1:
                bbox = data[str(i)]
                bboxes.append(bbox)
                i += 1

            match[0] = bboxes

        return matching_ims

    def get_brandoptions(self):
        brands = []
        for brand in self.db.collection_names():
            brands.append(brand)

        brand_options = []
        default = "Choose:"
        brand_options.append(default)
        for brand in brands:
            brand_options.append(brand)

        return brand_options

    def purge_old_entries(self):
        for coll in self.db.collection_names():
            self.db[coll].delete_one({"name": self.im_name})
