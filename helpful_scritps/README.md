## Merge dataset outputed by labeler
[merge_coco.py](merge_coco.py) - Merge multiple COCO JSON files into one.
```bash
python merge_coco.py dataset1 dataset2 --output merged_dataset
```

Dataset structure:
```bash
dataset1/
    ├── frames/
    │   ├── 00000.jpg
    │   └── 00001.jpg
    └── labels.json

dataset2/
    ├── frames/
    │   ├── 00000.jpg
    │   └── 00001.jpg
    └── labels.json
```

## Convert COCO to YOLO format
[convert_coco_yolo.py](convert_coco_yolo.py)
```bash
python convert_coco_yolo.py dataset
```
Result dataset structure:
```bash
dataset1/
    ├── frames/
    │   ├── 00000.jpg
    │   └── 00001.jpg
    └── labels.json
    └── yolo/
        ├── 00000.txt
        └── 00001.txt
```
