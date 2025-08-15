#!/usr/bin/env python3
"""
COCO Dataset Merger Script

Usage: python merge_coco.py dataset1 dataset2 dataset3 ...

Merges multiple COCO datasets with the following directory structure:
├── <video_name>
│   ├── frames/  (contains images)
│   ├── labels.json  (COCO format annotations)

Features:
- Handles file name collisions by prefixing images with "<video_name>_"
- Resolves class ID mismatches while preserving class names
- Merges all unique classes from all datasets
- Outputs merged labels.json and copied images to merged_dataset/
"""

import json
import os
import sys
import shutil
from pathlib import Path
from collections import defaultdict
import argparse


def load_coco_dataset(dataset_path):
    """Load COCO dataset from directory."""
    dataset_path = Path(dataset_path)
    labels_file = dataset_path / "labels.json"
    frames_dir = dataset_path / "frames"
    
    if not labels_file.exists():
        raise FileNotFoundError(f"labels.json not found in {dataset_path}")
    if not frames_dir.exists():
        raise FileNotFoundError(f"frames directory not found in {dataset_path}")
    
    with open(labels_file, 'r') as f:
        coco_data = json.load(f)
    
    return coco_data, frames_dir


def create_class_mapping(datasets_info):
    """
    Create a mapping from old class IDs to new unified class IDs.
    Uses the first dataset as the reference for class IDs.
    """
    # Collect all unique class names and their IDs from all datasets
    all_classes = {}  # class_name -> (first_seen_id, datasets_with_this_class)
    dataset_class_maps = []  # List of {old_id -> new_id} for each dataset
    
    for i, (video_name, coco_data, _) in enumerate(datasets_info):
        dataset_classes = {cat['name']: cat['id'] for cat in coco_data['categories']}
        dataset_class_maps.append({})
        
        for class_name, old_id in dataset_classes.items():
            if class_name not in all_classes:
                # First time seeing this class
                if i == 0:
                    # For the first dataset, keep original IDs
                    new_id = old_id
                else:
                    # For subsequent datasets, assign new ID
                    used_ids = set(info[0] for info in all_classes.values())
                    new_id = max(used_ids, default=0) + 1
                
                all_classes[class_name] = (new_id, [video_name])
            else:
                # Class already exists, use existing new_id
                new_id = all_classes[class_name][0]
                all_classes[class_name][1].append(video_name)
            
            dataset_class_maps[i][old_id] = new_id
    
    # Create final categories list
    final_categories = []
    for class_name, (new_id, _) in all_classes.items():
        final_categories.append({
            'id': new_id,
            'name': class_name,
            'supercategory': ''  # Default supercategory
        })
    
    final_categories.sort(key=lambda x: x['id'])
    
    return dataset_class_maps, final_categories, all_classes


def merge_datasets(dataset_paths, output_dir):
    """Main function to merge COCO datasets."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Create output directories
    output_frames_dir = output_dir / "frames"
    output_frames_dir.mkdir(exist_ok=True)
    
    # Load all datasets
    datasets_info = []
    for dataset_path in dataset_paths:
        video_name = Path(dataset_path).name
        coco_data, frames_dir = load_coco_dataset(dataset_path)
        datasets_info.append((video_name, coco_data, frames_dir))
        print(f"Loaded dataset: {video_name} with {len(coco_data['images'])} images")
    
    # Create class mapping
    dataset_class_maps, final_categories, all_classes = create_class_mapping(datasets_info)
    
    print(f"\nClass mapping summary:")
    for class_name, (new_id, datasets) in all_classes.items():
        print(f"  {class_name} -> ID {new_id} (found in: {', '.join(datasets)})")
    
    # Initialize merged dataset structure
    merged_dataset = {
        'info': {
            'description': 'Merged COCO dataset',
            'version': '1.0',
            'year': 2024,
        },
        'licenses': [],
        'images': [],
        'annotations': [],
        'categories': final_categories
    }
    
    # Track ID counters
    next_image_id = 1
    next_annotation_id = 1
    image_id_mapping = {}  # old_image_id -> new_image_id for each dataset
    
    # Process each dataset
    for dataset_idx, (video_name, coco_data, frames_dir) in enumerate(datasets_info):
        print(f"\nProcessing dataset: {video_name}")
        
        # Create image ID mapping for this dataset
        dataset_image_mapping = {}
        
        # Process images
        for img_info in coco_data['images']:
            old_image_id = img_info['id']
            old_filename = img_info['file_name']
            
            # Create new filename with prefix
            new_filename = f"{video_name}_{old_filename}"
            
            # Copy image file
            old_image_path = frames_dir / old_filename
            new_image_path = output_frames_dir / new_filename
            
            if old_image_path.exists():
                shutil.copy2(old_image_path, new_image_path)
            else:
                print(f"Warning: Image file {old_image_path} not found")
            
            # Create new image info
            new_image_info = img_info.copy()
            new_image_info['id'] = next_image_id
            new_image_info['file_name'] = new_filename
            
            dataset_image_mapping[old_image_id] = next_image_id
            merged_dataset['images'].append(new_image_info)
            
            next_image_id += 1
        
        # Process annotations
        class_mapping = dataset_class_maps[dataset_idx]
        
        for ann_info in coco_data['annotations']:
            old_image_id = ann_info['image_id']
            old_category_id = ann_info['category_id']
            
            # Skip if image was not found
            if old_image_id not in dataset_image_mapping:
                continue
            
            # Create new annotation
            new_ann_info = ann_info.copy()
            new_ann_info['id'] = next_annotation_id
            new_ann_info['image_id'] = dataset_image_mapping[old_image_id]
            new_ann_info['category_id'] = class_mapping[old_category_id]
            
            merged_dataset['annotations'].append(new_ann_info)
            next_annotation_id += 1
        
        print(f"  Processed {len(coco_data['images'])} images and {len(coco_data['annotations'])} annotations")
    
    # Save merged dataset
    output_labels_path = output_dir / "labels.json"
    with open(output_labels_path, 'w') as f:
        json.dump(merged_dataset, f, indent=2)
    
    print(f"\nMerging complete!")
    print(f"Output directory: {output_dir}")
    print(f"Total images: {len(merged_dataset['images'])}")
    print(f"Total annotations: {len(merged_dataset['annotations'])}")
    print(f"Total categories: {len(merged_dataset['categories'])}")
    print(f"Images saved to: {output_frames_dir}")
    print(f"Labels saved to: {output_labels_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Merge multiple COCO datasets with collision handling and class mapping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python merge_coco.py dataset1 dataset2 dataset3
  python merge_coco.py video1/ video2/ video3/ --output merged_dataset/

Directory structure expected:
  dataset1/
  ├── frames/           # Directory containing images
  └── labels.json       # COCO format annotations
        """
    )
    
    parser.add_argument('datasets', nargs='+', 
                       help='Paths to dataset directories')
    parser.add_argument('-o', '--output', default='merged_dataset',
                       help='Output directory for merged dataset (default: merged_dataset)')
    
    args = parser.parse_args()
    
    # Validate input directories
    for dataset_path in args.datasets:
        if not os.path.isdir(dataset_path):
            print(f"Error: {dataset_path} is not a valid directory")
            sys.exit(1)
    
    try:
        merge_datasets(args.datasets, args.output)
    except Exception as e:
        print(f"Error during merging: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()