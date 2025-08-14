#!/bin/bash
folder=$(basename "$PWD")

cd frames
rename "s/^/${folder}_/" *

cd ../yolo
rename "s/^/${folder}_/" *

echo "Done!"
