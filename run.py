import subprocess as s
import shlex as sh


dir = "/Users/dtrenhaile/Desktop/mongo_testdir"  # path to your top directory for images to be annotated
cat = "ford"  # corresponds to the subdirectory of the car brand you wish to annotate
keys = "/Users/dtrenhaile/projects/object_detection/datasets/BBox-Label-Tool/v7/keys/cars.json"

s.call(sh.split("python gui.py --dir " + dir + " --cat " + cat + " --keys " + keys))
