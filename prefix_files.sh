#!/bin/bash

# Get the folder name from current directory
folder_name=$(basename "$(pwd)")

# Change to the folder
cd "$folder_path" || exit 1

# Rename all files in the folder using rename command
rename "s/^(?!${folder_name}_)/${folder_name}_/" yolo/*.txt
rename "s/^(?!${folder_name}_)/${folder_name}_/" frames/*.jpg

echo "Done!"
