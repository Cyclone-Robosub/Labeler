import fiftyone as fo
import sys
import argparse

def visualize_coco_with_fiftyone(images_dir, annotations_file):
    """
    Load and visualize COCO dataset using FiftyOne
    
    Args:
        images_dir: Path to directory containing images
        annotations_file: Path to COCO JSON annotations file
    """
    
    # Import COCO dataset
    dataset = fo.Dataset.from_dir(
        dataset_type=fo.types.COCODetectionDataset,
        data_path=images_dir,
        labels_path=annotations_file,
        name="coco_visualization"
    )
    
    print(f"Loaded {len(dataset)} samples")
    print(f"Classes: {dataset.distinct('detections.detections.label')}")
    
    # Launch interactive viewer
    session = fo.launch_app(dataset, port=5151)
    
    return dataset, session

def quick_stats(dataset):
    """Print quick statistics about the dataset"""
    print(f"\nDataset Statistics:")
    print(f"Total samples: {len(dataset)}")
    print(f"Samples with detections: {len(dataset.match(fo.ViewField('detections.detections').length() > 0))}")
    
    # Class distribution
    labels = dataset.values('detections.detections.label', unwind=True)
    from collections import Counter
    label_counts = Counter(labels)
    
    print(f"\nClass distribution:")
    for label, count in label_counts.items():
        print(f"  {label}: {count}")

# Usage
if __name__ == "__main__":
    images_dir = sys.argv[1]
    annotations_file = sys.argv[2]
    
    # Visualize dataset
    dataset, session = visualize_coco_with_fiftyone(images_dir, annotations_file)
    
    # Print statistics
    quick_stats(dataset)
    
    # Keep the session running
    print("FiftyOne app is running at http://localhost:5151")
    print("Press Ctrl+C to stop")
    session.wait()