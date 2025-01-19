#! /usr/bin/python

import os

for filename in os.listdir("."):
    if filename.endswith("po"):
        print(filename)
        os.system(
            "msgmerge --no-fuzzy-matching "
            + filename
            + " mnemosyne.pot -o "
            + filename
        )
