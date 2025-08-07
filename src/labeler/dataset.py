import json
import cv2
import numpy as np
import os
from datetime import datetime

"""
This module creates a COCO formated object detection dataset for 1 object.
"""

class COCODataset:
    def __init__(self, name="multi_object_detection_dataset"):
        self.coco_dataset = {
            "info": {
                "year": 2025,
                "version": "1.0",
                "description": name,
                "date_created": datetime.now().isoformat()
            },
            "licenses": [],
            "images": [],
            "annotations": [],
            "categories": []
        }
        self.category_id_map = {}  # Maps object_name -> category_id
        self.next_category_id = 1
    
    def add_category(self, object_name: str) -> int:
        """Add a new category and return its ID"""
        if object_name in self.category_id_map:
            return self.category_id_map[object_name]
        
        category_id = self.next_category_id
        self.next_category_id += 1
        
        self.coco_dataset["categories"].append({
            "id": category_id,
            "name": object_name,
            "supercategory": "object"
        })
        
        self.category_id_map[object_name] = category_id
        return category_id

    def mask_to_bbox(self, mask):
        """Convert binary mask to bounding box [x, y, width, height]"""
        rows, cols = np.where(mask > 0)
        if len(rows) == 0:
            return [0, 0, 0, 0]
        
        x_min, x_max = cols.min(), cols.max()
        y_min, y_max = rows.min(), rows.max()
        
        return [int(x_min), int(y_min), int(x_max - x_min + 1), int(y_max - y_min + 1)]

    def convert_mask_to_annotation(self, mask, category_id: int):
        """
        Convert a binary mask to COCO annotation format.
        """
        # Get bounding box coordinates
        x, y, w, h = self.mask_to_bbox(mask)
        area = w * h

        return {
            "id": len(self.coco_dataset["annotations"]) + 1,
            "image_id": None,  # To be set when adding the image
            "category_id": category_id,
            "segmentation": None,
            "area": area,
            "bbox": [x, y, w, h],
            "iscrowd": 0
        }
    
    def add_sam_mask(self, mask, image_path, object_name: str):
        """
        Add a SAM mask to the dataset.
        
        Args:
            mask (numpy.ndarray): Binary mask of the object.
            image_path (str): Path to the corresponding image.
            object_name (str): Name of the object category.
        """
        mask = np.squeeze(mask)
        
        # Get or create category ID for this object
        category_id = self.add_category(object_name)
        
        annotation = self.convert_mask_to_annotation(mask, category_id)
        
        self.add_image(image_path, mask.shape[1], mask.shape[0], annotation)

    def add_image(self, image_path, width, height, annotation=None):
        """
        Add an image to the dataset.

        Args:
            image_path (str): Path to the image file.
            annotations (list, optional): List of annotations for the image.
        """
        image_id = len(self.coco_dataset["images"]) + 1
        self.coco_dataset["images"].append({
            "id": image_id,
            "file_name": os.path.basename(image_path),
            "width": width,
            "height": height
        })

        if annotation:
            # expect a single annotation for the single object
            annotation["image_id"] = image_id
            self.coco_dataset["annotations"].append(annotation)

    def export_to_json(self, output_path):
        """
        Export the dataset to a JSON file.

        Args:
            output_path (str): Path to save the JSON file.
        """
        with open(output_path, 'w') as f:
            json.dump(self.coco_dataset, f, indent=4)
        print(f"Dataset exported to {output_path}")
