#!/bin/bash

# Script to process all directories in the current folder
# For each directory: run COCO to YOLO conversion and prefix files

# Loop through all directories in the current folder
for dir in */; do
    # Check if it's actually a directory
    if [ -d "$dir" ]; then
        echo "Processing directory: $dir"
        
        # Change into the directory
        cd "$dir"
        
        # Run the COCO to YOLO conversion
        echo "  Running COCO to YOLO conversion..."
        if python ../../legacy/convert_coco_yolo.py .; then
            echo "  ✓ COCO to YOLO conversion completed"
        else
            echo "  ✗ COCO to YOLO conversion failed"
        fi
        
        # Run the prefix files script
        echo "  Running prefix files script..."
        if ../../prefix_files.sh; then
            echo "  ✓ Prefix files script completed"
        else
            echo "  ✗ Prefix files script failed"
        fi
        
        # Return to the original directory
        cd ".."
        
        echo "  Finished processing $dir"
        echo ""
    fi
done

echo "All directories processed!"