from __future__ import division
from tkinter import *
import json
import string
import argparse
import os
from functions import FunctionController
from convert import Converter

ap = argparse.ArgumentParser()
ap.add_argument("-d", "--dir", required=True, help="top pull directory")
ap.add_argument("-b", "--cat", required=True, help="the car brand you wish to analyze; corresponds to a subdir of -d")
ap.add_argument("-k", "--keys", required=True, help="path to json key bindings for categories")
args = vars(ap.parse_args())


class GuiController:
    def __init__(self, parent):
        parent.title("LabelTool")
        self.frame = Frame(parent)
        self.frame.pack(fill=BOTH, expand=1)
        parent.resizable(width=FALSE, height=FALSE)
        self.fc = FunctionController(args["dir"])
        
        ########### vars ################
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        self.main_panel = None
        self.cur_frame = None
        self.tkimg = None
        self.total = 0
        self.prog = None
        self.nav_idx = None
        self.listframe = None
        self.listframe_rows = 0
        self.cat_frames = []
        self.cat_index = 0
        self.tkvars = []
        self.opt_menues = []
        self.err_menues = []
        self.err_frame = None
        self.err_msg = None
        self.disp = None

        self.hl = None
        self.vl = None

        self.bbox_list = []  # coordinates
        self.bbox_idlist = []
        self.bbox_id = None

        self.COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
        self.color_idx = 0
        self.brand_options = []
        self.default = "Choose:"
        self.in_path = ""

        self.construct_gui(parent)
        self.bind_keys(parent)

    def construct_gui(self, p):
        load_btn = Button(self.frame, text="Load", command=self.load_dir)
        load_btn.grid(row=0, column=2, sticky=E)

        self.main_panel = Canvas(self.frame, cursor="tcross")
        self.main_panel.bind("<Button-1>", self.mouse_click)
        self.main_panel.bind("<Motion>", self.mouse_move)
        p.bind("<Escape>", self.cancel_bbox)

        self.main_panel.grid(row=1, column=1, rowspan=4, sticky=W+N)

        label = Label(self.frame, text="BBox Categorizer:")
        label.grid(row=1, column=2, sticky=W+N)
        
        self.listframe = Frame(self.frame, width=175, height=180)
        self.listframe.grid_propagate(False)
        self.listframe.grid(row=2, column=2, sticky=N, padx=7)
        self.listframe.config(highlightbackground='black', highlightthickness=2)

        del_btn = Button(self.frame, text="Delete BBox", padx=7, pady=5, command=self.delete_bbox)
        del_btn.grid_propagate(False)
        del_btn.grid(row=3, column=2, sticky=E+W)

        convert_btn = Button(self.frame, text="Convert", padx=7, pady=5, command=self.convert)
        convert_btn.grid_propagate(False)
        convert_btn.grid(row=4, column=2, sticky=E+W+N)

        ctr_panel = Frame(self.frame)
        ctr_panel.grid(row=5, column=1, columnspan=2, sticky=W+E)
        prev_btn = Button(ctr_panel, text="<< Prev", width=10, command=self.prev_image)
        prev_btn.pack(side=LEFT, padx=5, pady=3)
        next_btn = Button(ctr_panel, text="Save >>", width=10, command=self.save_image)
        next_btn.pack(side=LEFT, padx=5, pady=3)
        self.prog = Label(ctr_panel, text="Progress:     /    ")
        self.prog.pack(side=LEFT, padx=5)

        # finicky; cursor stays inside entry box so navigation with hotkeys shows up there
        '''nav_label = Label(ctr_panel, text="Go to Image No.")
        nav_label.pack(side=LEFT, padx=5)
        self.nav_idx = Entry(ctr_panel, width=5)
        self.nav_idx.pack(side=LEFT)
        go_btn = Button(ctr_panel, text='Go', command=self.goto_image)
        go_btn.pack(side=LEFT)'''

        self.disp = Label(ctr_panel, text='')
        self.disp.pack(side=RIGHT)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(4, weight=1)

    def bind_keys(self, p):
        p.bind("2", self.save_image)
        p.bind("3", self.prev_image)
        p.bind("4", self.next_image)
        p.bind("<space>", self.skip_im)
        p.bind("<Up>", self.select_prev)
        p.bind("<Down>", self.select_next)

        with open(args["keys"]) as k:
            data = json.load(k)
        for l in list(string.ascii_lowercase):
            d = data[l]
            if d != "":
                p.bind(l, lambda event, s=d: self.update_tkvars(s))
                p.focus_set()
        for n in range(1, 11):
            i = str(n)
            try:
                d = data[i]
                if d != "":
                    p.bind(i, lambda event, s=d: self.update_tkvars(s))
            except KeyError:
                pass
            
    def mouse_click(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)

            bbox_entry = [x1, y1, x2, y2]

            ###############################################
            self.bbox_list.append(bbox_entry)
            self.bbox_idlist.append(self.bbox_id)
            self.bbox_id = None

            # pass x1 to verify bboxes
            self.append_bboxes(self.default, "new box")

        self.STATE['click'] = 1 - self.STATE['click']
        
    def mouse_move(self, event):
        self.disp.config(text='x: %d, y: %d' % (event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.main_panel.delete(self.hl)
            self.hl = self.main_panel.create_line(0, event.y, self.tkimg.width(), event.y, width=2)
            if self.vl:
                self.main_panel.delete(self.vl)
            self.vl = self.main_panel.create_line(event.x, 0, event.x, self.tkimg.height(), width=2)
        if 1 == self.STATE['click']:
            if self.bbox_id:
                self.main_panel.delete(self.bbox_id)
            self.bbox_id = self.main_panel.create_rectangle(self.STATE['x'], self.STATE['y'],
                                                          event.x, event.y,
                                                          width=2,
                                                          outline=self.COLORS[self.color_idx % len(self.COLORS)])
        
    def cancel_bbox(self, event=None):
        print("canceling")
        if 1 == self.STATE['click']:
            if self.bbox_id:
                self.main_panel.delete(self.bbox_id)
                self.bbox_id = None
                self.STATE['click'] = 0

    # interfering with listbox frames
    def delete_bbox(self, event=None):
        # print("delete_bbox")
        # print("cat_index: " + str(self.cat_index))
        self.main_panel.delete(self.bbox_idlist[self.cat_index])
        self.bbox_list.pop(self.cat_index)
        self.tkvars.pop(self.cat_index)
        self.bbox_idlist.pop(self.cat_index)

        cur = self.cur_frame
        for frame in self.cat_frames:
            if frame == cur:
                self.select_prev()
                self.cat_frames.remove(cur)
                cur.destroy()

    def change_image(self, prev_bboxes, prog_update):
        self.main_panel.config(width=max(self.tkimg.width(), 400), height=max(self.tkimg.height(), 400))
        self.main_panel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.prog.config(text="%04d/%04d" % (prog_update[0], prog_update[1]))

        brands = []
        bboxes = []
        for entry in prev_bboxes:
            for bbox in entry[0]:
                brands.append(entry[1])
                bboxes.append(bbox)

        i = 0
        while i < len(bboxes):
            bbox = bboxes[i]
            b = (bbox["left x"], bbox["top y"], bbox["right x"], bbox["bottom y"])
            print("change image get color")
            id = self.main_panel.create_rectangle(b[0], b[1], b[2], b[3], width=2,
                                                  outline=self.COLORS[self.color_idx % len(self.COLORS)])
            # self.bboxIdList
            self.bbox_list.append(tuple(b))
            self.bbox_idlist.append(id)

            # pass bbox["left x"] for bbox verification
            self.append_bboxes(brands[i], bbox["left x"])
            i += 1

    def append_bboxes(self, brand, temp):
        self.listframe_rows += 1
        cat_frame = Frame(self.listframe, width=170, height=29)
        cat_frame.grid_propagate(False)
        cat_frame.grid(row=self.listframe_rows, column=1, columnspan=2, sticky=W+E+N)

        cat_frame.grid_columnconfigure(1, weight=1)
        cat_frame.grid_columnconfigure(2, weight=1)

        text = str(temp)
        # text = "bbox " + str(self.listframe_rows)
        print("color_idx: " + str(self.color_idx))
        new_cat_label = Label(cat_frame, text=text,
                              fg=self.COLORS[self.color_idx % len(self.COLORS)])
        new_cat_label.grid(row=1, column=1, sticky=W)

        tkvar = StringVar(cat_frame)
        tkvar.set(brand)

        menu = OptionMenu(cat_frame, tkvar, *self.brand_options)
        menu.grid(row=1, column=2, sticky=E)

        self.cat_frames.append(cat_frame)
        self.tkvars.append(tkvar)
        self.opt_menues.append(menu)
        print("     plus 1")
        self.color_idx += 1

        if len(self.cat_frames) == 1:
            self.select_frame(0)

    def select_frame(self, index):
        l = len(self.cat_frames)

        if l - 1 < index:
            self.cat_index = 0
        elif index == -1:
            self.cat_index = l - 1
        else:
            self.cat_index = index

        if l > 0:
            if self.cur_frame is not None:
                self.cur_frame.config(bg="white")
            frame = self.cat_frames[self.cat_index]
            frame.config(bg="blue")
            self.cur_frame = frame

    def select_next(self, event=None):
        self.select_frame(self.cat_index + 1)

    def select_prev(self, event=None):
        self.select_frame(self.cat_index - 1)

    def update_tkvars(self, brand):
        print("brand: " + str(brand))
        if len(self.tkvars) > 0:
            tkvar = self.tkvars[self.cat_index]
            tkvar.set(brand)
            self.select_next()

    def rinse(self):
        for idx in range(len(self.bbox_idlist)):
            # delete = self.bbox_idlist[idx]
            # print("bbox_idlist: " + str(len(self.bbox_idlist)))
            self.main_panel.delete(self.bbox_idlist[idx])
        self.delete_frames()
        self.cat_frames = []
        self.cat_index = 0
        self.listframe_rows = 0
        self.cur_frame = None
        self.opt_menues = []
        self.err_menues = []
        self.tkvars = []
        self.bbox_list = []
        self.bbox_idlist = []
        self.color_idx = 0

        if self.err_msg is not None:
            self.err_msg.destroy()
            self.err_msg = None

    def get_annotations(self):
        if len(self.bbox_list) > 0:
            annotations = []
            brand_pairings = []
            catless = []

            i = 0
            for tkvar in self.tkvars:
                brand = tkvar.get()
                if brand == self.default:
                    catless.append(i)
                else:
                    append = True
                    for ann in annotations:
                        s_brand = ann[0]
                        if s_brand == brand:
                            append = False

                    if append:
                        annotations.append([brand, []])
                    brand_pairings.append([brand, self.bbox_list[i]])
                i += 1

            if len(catless) > 0:
                self.err_missingcats(catless)
                return False

            for pair in brand_pairings:
                for cat in annotations:
                    if pair[0] == cat[0]:
                        cat[1].append(pair[1])

            return annotations

        else:
            print("[INFO] No bounding boxes; image was not saved")
            return False

    '''def get_color(self, changing_image=False):
        idx = 0
        if len(self.USED_COLORS) > 0:
            for u_c in self.USED_COLORS:
                for c in self.COLORS:
                    if u_c == c:
                        idx += 1

        color = self.COLORS[idx % len(self.COLORS)]
        if len(self.bbox_list) > idx and not changing_image:
            self.USED_COLORS.append(color)
        print("     color: " + str(color))
        print("     bbox length: " + str(len(self.bbox_list)))
        return color'''

    def delete_frames(self, idx=-1):
        if idx > -1:
            self.cat_frames[idx].destroy()
            return
        for frame in self.cat_frames:
            frame.destroy()

    def err_missingcats(self, c):
        self.err_msg = Message(self.frame, text="**Please specify a db collection for the bbox(es)**", width=170)
        self.err_msg.config(fg='red', justify="center")
        self.err_msg.grid(row=5, column=2, sticky=N + E + W)
        for i in c:
            err_menu = self.opt_menues[i]
            err_menu.config(bg='red', highlightthickness=3.9)
            self.err_menues.append(err_menu)

    #########################################
    # Communication with functionController #
    #########################################
    def load_dir(self, event=None):
        self.brand_options = self.fc.get_brandoptions()
        self.total, self.in_path = self.fc.load_dir(args["dir"], args["cat"])
        self.next_image()

    def save_image(self, event=None):
        for menu in self.err_menues:
            menu.config(bg='white', highlightthickness=0)
        annotations = self.get_annotations()
        if annotations is False:
            return
        self.fc.save_image(annotations)
        self.next_image()

    def prev_image(self, event=None):
        try:
            self.tkimg, prev_bboxes, prog_update = self.fc.prev_image()
        except TypeError:
            return
        if self.tkimg is not None:
            self.rinse()
            self.change_image(prev_bboxes, prog_update)

    def next_image(self, event=None, idx=0):
        im, prev_bboxes, prog_update = self.fc.next_image(idx=idx)
        if im is not None:
            self.tkimg = im
            self.rinse()
            self.change_image(prev_bboxes, prog_update)

    def skip_im(self, event=None):
        self.fc.skip_im()
        self.next_image()

    # finicky; cursor stays inside entry box so navigation with hotkeys shows up there
    '''def goto_image(self, event=None):
        idx = int(self.nav_idx.get())
        if 1 <= idx <= self.total:
            self.next_image(idx=idx)'''

    ###########################################################
    # Convert this script's coordinate outputs to YOLO format #
    ###########################################################

    def convert(self, event=None):
        if self.in_path == "":
            print("[INFO] No images have been loaded yet!")
            print()
        else:
            outpath = os.path.join(args["dir"], "converted")
            converter = Converter(self.in_path, outpath, 10)
            converter.convert()


if __name__ == '__main__':
    root = Tk()
    tool = GuiController(root)
    root.resizable(width=True, height=True)
    root.mainloop()
