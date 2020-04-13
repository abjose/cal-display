#!/bin/bash

# query calendar and generate the svg
python3 gen_image.py

# convert to png with inkscape
inkscape -z -w 800 -h 600 output.svg -e output.png
