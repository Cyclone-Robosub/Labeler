# COCO Dataset Export Fix

## Problem Identified
The exported COCO dataset had **duplicate image entries** for the same frame files, causing visualization tools to only show annotations for the first occurrence of each image.

**Previous Issue (Incorrect)**:
```json
{
  "images": [
    {"id": 1, "file_name": "00000.jpg"},  // First occurrence
    {"id": 2, "file_name": "00000.jpg"},  // DUPLICATE - different ID
    {"id": 3, "file_name": "00001.jpg"},  // First occurrence  
    {"id": 4, "file_name": "00001.jpg"}   // DUPLICATE - different ID
  ],
  "annotations": [
    {"id": 1, "image_id": 1, "category_id": 1},  // Red object on image 1
    {"id": 2, "image_id": 2, "category_id": 2},  // Green object on "different" image 2 (same file!)
  ]
}
```

**Visualization Problem**: Tools see `00000.jpg` twice with different IDs, often only displaying annotations from the first image entry (ID 1), missing annotations from the "duplicate" entry (ID 2).

## Root Cause
The `add_sam_mask` method was calling `add_image` for each object separately, creating new image entries even when the image file already existed in the dataset.

**Problematic Code Flow**:
```python
# For each frame with multiple objects:
for obj_id, mask in frame_masks.items():
    coco_dataset.add_sam_mask(mask, "00000.jpg", object_name)
    # Each call creates NEW image entry for same file!
```

## Solution Implemented

### 1. Image Deduplication System
Added tracking to prevent duplicate image entries:

```python
class COCODataset:
    def __init__(self):
        self.image_id_map = {}      # filename -> image_id mapping
        self.next_image_id = 1      # Sequential image ID counter
        self.next_annotation_id = 1 # Sequential annotation ID counter
```

### 2. Smart Image Management
```python
def get_or_create_image(self, image_path: str, width: int, height: int) -> int:
    """Get existing image ID or create new image entry. Returns image_id."""
    filename = os.path.basename(image_path)
    
    # Check if image already exists
    if filename in self.image_id_map:
        return self.image_id_map[filename]  # Return existing ID
    
    # Create new image entry only if needed
    image_id = self.next_image_id
    self.next_image_id += 1
    # ... add to dataset and map
    return image_id
```

### 3. Updated Export Flow
```python
def add_sam_mask(self, mask, image_path, object_name: str):
    # Get or create image (deduplicates automatically)
    image_id = self.get_or_create_image(image_path, width, height)
    
    # Create annotation linked to correct image
    annotation = self.convert_mask_to_annotation(mask, category_id)
    annotation["image_id"] = image_id
    
    # Add annotation to dataset
    self.coco_dataset["annotations"].append(annotation)
```

## Expected Correct Output

**After Fix (Correct)**:
```json
{
  "images": [
    {"id": 1, "file_name": "00000.jpg", "width": 380, "height": 250},
    {"id": 2, "file_name": "00001.jpg", "width": 380, "height": 250},
    {"id": 3, "file_name": "00002.jpg", "width": 380, "height": 250}
  ],
  "annotations": [
    {"id": 1, "image_id": 1, "category_id": 1, "bbox": [33, 171, 47, 50]},  // Red on frame 0
    {"id": 2, "image_id": 1, "category_id": 2, "bbox": [232, 158, 41, 30]}, // Green on frame 0 
    {"id": 3, "image_id": 2, "category_id": 1, "bbox": [29, 163, 47, 51]},  // Red on frame 1
    {"id": 4, "image_id": 2, "category_id": 2, "bbox": [228, 152, 41, 30]}  // Green on frame 1
  ],
  "categories": [
    {"id": 1, "name": "red", "supercategory": "object"},
    {"id": 2, "name": "green", "supercategory": "object"}
  ]
}
```

## Key Improvements

### ✅ **Proper Image Management**
- Each image file appears exactly once in the images array
- Multiple objects per image are handled correctly
- Sequential image IDs without gaps

### ✅ **Correct Annotation Linking**
- All annotations for the same image reference the same image_id
- Multiple objects per frame properly grouped
- Visualization tools will show all objects per image

### ✅ **COCO Standard Compliance**
- Follows COCO format specifications exactly
- Compatible with all COCO visualization and training tools
- Proper relationship between images, annotations, and categories

### ✅ **Visualization Compatibility**
- Tools like COCO API, FiftyOne, Labelbox will display all objects
- No more missing annotations due to duplicate image entries
- Proper multi-object visualization per frame

## Testing the Fix

**Before**: Export dataset → visualize → only see first object per frame  
**After**: Export dataset → visualize → see all objects per frame correctly

The fix ensures that your multi-object annotations are properly exported and will be visualized correctly by standard COCO tools!
