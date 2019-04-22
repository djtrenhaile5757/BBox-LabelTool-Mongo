import subprocess as s
import shlex as sh


dir = "/Users/dtrenhaile/Desktop/mongo_testdir"  # path to your top directory for images to be annotated
brand = "ford"  # corresponds to the subdirectory of the car brand you wish to annotate
s.call(sh.split("python gui.py --keys key_bindings.json --dir " + dir + " --brand " + brand))
