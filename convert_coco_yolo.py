import json
import os
from pathlib import Path
import sys

def coco_to_yolo_bbox(coco_bbox, img_width, img_height):
    """
    Convert COCO bounding box format to YOLO format
    
    COCO format: [x_min, y_min, width, height] (absolute coordinates)
    YOLO format: [x_center, y_center, width, height] (normalized 0-1)
    
    Args:
        coco_bbox: List [x_min, y_min, width, height] in pixels
        img_width: Image width in pixels
        img_height: Image height in pixels
    
    Returns:
        List [x_center, y_center, width, height] normalized to 0-1
    """
    x_min, y_min, bbox_width, bbox_height = coco_bbox
    
    # Calculate center coordinates
    x_center = x_min + bbox_width / 2
    y_center = y_min + bbox_height / 2
    
    # Normalize to 0-1 range
    x_center_norm = x_center / img_width
    y_center_norm = y_center / img_height
    width_norm = bbox_width / img_width
    height_norm = bbox_height / img_height
    
    return [x_center_norm, y_center_norm, width_norm, height_norm]

def convert_coco_to_yolo(coco_json_path, output_dir, class_mapping=None):
    """
    Convert COCO annotations to YOLO format
    
    Args:
        coco_json_path: Path to COCO JSON annotation file
        output_dir: Directory to save YOLO format annotations
        class_mapping: Optional dict to map COCO category IDs to YOLO class IDs
    """
    # Load COCO annotations
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create image info lookup
    images = {img['id']: img for img in coco_data['images']}
    
    # Create category mapping if not provided
    if class_mapping is None:
        categories = {cat['id']: idx for idx, cat in enumerate(coco_data['categories'])}
    else:
        categories = class_mapping
    
    # Group annotations by image
    annotations_by_image = {}
    for ann in coco_data['annotations']:
        img_id = ann['image_id']
        if img_id not in annotations_by_image:
            annotations_by_image[img_id] = []
        annotations_by_image[img_id].append(ann)
    
    # Convert each image's annotations
    for img_id, annotations in annotations_by_image.items():
        img_info = images[img_id]
        img_width = img_info['width']
        img_height = img_info['height']
        img_filename = img_info['file_name']
        
        # Create corresponding .txt filename
        txt_filename = Path(img_filename).stem + '.txt'
        txt_path = output_dir / txt_filename
        
        # Convert annotations for this image
        yolo_annotations = []
        for ann in annotations:
            # Skip if annotation doesn't have bbox or is crowd
            if 'bbox' not in ann or ann.get('iscrowd', 0):
                continue
            
            # Get class ID
            coco_cat_id = ann['category_id']
            if coco_cat_id not in categories:
                print(f"Warning: Category ID {coco_cat_id} not found in mapping")
                continue
            
            yolo_class_id = categories[coco_cat_id]
            
            # Convert bbox
            coco_bbox = ann['bbox']
            yolo_bbox = coco_to_yolo_bbox(coco_bbox, img_width, img_height)
            
            # Format: class_id x_center y_center width height
            yolo_line = f"{yolo_class_id} {' '.join(map(str, yolo_bbox))}"
            yolo_annotations.append(yolo_line)
        
        # Write to file
        with open(txt_path, 'w') as f:
            f.write('\n'.join(yolo_annotations))
        
        if yolo_annotations:
            print(f"Converted {len(yolo_annotations)} annotations for {img_filename}")

def create_yolo_yaml(coco_json_path, yaml_path):
    """
    Create YOLO dataset YAML configuration file
    
    Args:
        coco_json_path: Path to COCO JSON annotation file
        yaml_path: Output path for YAML file
    """
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
    
    # Extract class names
    class_names = [cat['name'] for cat in sorted(coco_data['categories'], key=lambda x: x['id'])]
    
    yaml_content = f"""# YOLOv8 dataset configuration
# Generated from COCO annotations

# Dataset paths (update these to your actual paths)
path: ./dataset  # dataset root dir
train: images/train  # train images (relative to 'path')
val: images/val      # val images (relative to 'path')
test: images/test    # test images (optional, relative to 'path')

# Classes
nc: {len(class_names)}  # number of classes
names: {class_names}  # class names
"""
    
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    
    print(f"Created YOLO YAML config at {yaml_path}")

# Example usage
if __name__ == "__main__":
    
    # Get folder name from command line arguments
    if len(sys.argv) < 2:
        print("Usage: python convert_coco_yolo.py <folder_name>")
        sys.exit(1)
    
    folder_name = sys.argv[1]
    
    # Example usage
    coco_json_path = f"{folder_name}/labels.json"
    output_dir = f"{folder_name}/yolo"
    # yaml_path = f"{folder_name}/dataset.yaml"
    
    # Convert annotations
    convert_coco_to_yolo(coco_json_path, output_dir)
    
    # Create YAML config
    # create_yolo_yaml(coco_json_path, yaml_path)
    
    print("\nConversion complete!")
    print(f"YOLO annotations saved to: {output_dir}")
    # print(f"YOLO config saved to: {yaml_path}")
    
    # Optional: Create custom class mapping
    # custom_mapping = {1: 0, 2: 1, 3: 2}  # Maps COCO cat_id to YOLO class_id
    # convert_coco_to_yolo(coco_json_path, output_dir, custom_mapping)