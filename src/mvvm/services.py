"""
Services layer - business logic and external integrations
These services are UI-agnostic and can be reused across different frontends
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from .models import VideoInfo, Point, Mask, AnnotationSession
from ..labeler.model import Labeler  # Import existing SAM2 labeler
from ..labeler.dataset import COCODataset


class VideoService:
    """Service for video operations"""
    
    def __init__(self):
        self.cap: Optional[cv2.VideoCapture] = None
        self.current_video: Optional[VideoInfo] = None
    
    def load_video(self, video_path: str) -> VideoInfo:
        """Load a video file and return video information"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Extract video information
        video_info = VideoInfo(
            path=video_path,
            width=int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=self.cap.get(cv2.CAP_PROP_FPS),
            total_frames=int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        )
        video_info.duration = video_info.total_frames / video_info.fps if video_info.fps > 0 else 0
        
        self.current_video = video_info
        return video_info
    
    def get_frame(self, frame_index: int) -> Optional[np.ndarray]:
        """Get a specific frame from the video"""
        if not self.cap or not self.current_video:
            return None
        
        # Ensure frame index is within bounds
        frame_index = max(0, min(frame_index, self.current_video.total_frames - 1))
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.cap.read()
        
        return frame if ret else None
    
    def extract_frames_to_directory(self, start_frame: int, output_dir: str) -> List[str]:
        """Extract frames from start_frame to end and save to directory"""
        if not self.cap or not self.current_video:
            raise ValueError("No video loaded")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Clear existing frames
        for f in os.listdir(output_dir):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                os.remove(os.path.join(output_dir, f))
        
        frame_paths = []
        
        # SAM2 expects simple numeric filenames without prefixes
        frame_counter = 0
        for frame_idx in range(start_frame, self.current_video.total_frames):
            frame = self.get_frame(frame_idx)
            if frame is not None:
                # Use simple numeric filename that SAM2 expects
                filename = f"{frame_counter:05d}.jpg"
                filepath = os.path.join(output_dir, filename)
                cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
                frame_paths.append(filename)  # Store just the filename for later reference
                frame_counter += 1
        
        return frame_paths
    
    def cleanup(self):
        """Clean up video resources"""
        if self.cap:
            self.cap.release()
        self.cap = None
        self.current_video = None


class AnnotationService:
    """Service for handling SAM2 annotations"""
    
    def __init__(self, model_path: str = "sam2_checkpoint/sam2.1_hiera_large.pt"):
        self.model_path = model_path
        self.labeler: Optional[Labeler] = None
        self.frame_dir: Optional[str] = None
    
    def initialize_for_video(self, frame_dir: str):
        """Initialize SAM2 labeler for a video"""
        self.labeler = Labeler(self.model_path)
        self.labeler.init_inference_state(video_dir=frame_dir)
        self.frame_dir = frame_dir
    
    def add_point_annotation(self, point: Point, all_points_for_object: List[Point]) -> Mask:
        """Add a point annotation and return the generated mask using all points for the object"""
        if not self.labeler:
            raise ValueError("Annotation service not initialized")
        
        # Convert all points for this object to numpy arrays
        points = np.array([[p.x, p.y] for p in all_points_for_object], dtype=np.float32)
        labels = np.array([p.label for p in all_points_for_object], dtype=np.int32)
        
        _, mask_data = self.labeler.select_objects(
            points=points,
            labels=labels,
            ann_obj_id=point.object_id,
            ann_frame_idx=point.frame_index
        )
        
        return Mask(
            mask_data=mask_data,
            object_id=point.object_id,
            frame_index=point.frame_index
        )
    
    def propagate_annotations(self) -> Dict[int, Dict[int, Mask]]:
        """Run SAM2 propagation through the video"""
        if not self.labeler:
            raise ValueError("Annotation service not initialized")
        
        self.labeler.run_through_video()
        
        # Convert SAM2 results to our mask format
        masks_by_frame = {}
        for frame_idx, obj_masks in self.labeler.video_segments.items():
            masks_by_frame[frame_idx] = {}
            for obj_id, mask_data in obj_masks.items():
                masks_by_frame[frame_idx][obj_id] = Mask(
                    mask_data=mask_data,
                    object_id=obj_id,
                    frame_index=frame_idx
                )
        
        return masks_by_frame


class ExportService:
    """Service for exporting annotations"""
    
    def __init__(self):
        pass
    
    def export_to_coco(self, session: AnnotationSession, output_path: str):
        """Export annotation session to COCO format"""
        if not session.video_info:
            raise ValueError("No video information available")
        
        # Create COCO dataset
        dataset_name = f"{os.path.basename(session.video_info.path)}_annotations"
        coco_dataset = COCODataset(dataset_name)
        
        # Add masks to dataset
        for absolute_frame_idx, frame_masks in session.masks.items():
            # Convert absolute frame index to relative (for extracted frames)
            relative_frame_idx = absolute_frame_idx - session.start_frame
            
            for obj_id, mask in frame_masks.items():
                # Get object name
                object_name = "unknown"
                if obj_id in session.objects:
                    object_name = session.objects[obj_id].name
                
                # Map relative frame index to extracted frame filename
                if 0 <= relative_frame_idx < len(session.frame_paths):
                    image_filename = session.frame_paths[relative_frame_idx]
                    
                    coco_dataset.add_sam_mask(
                        mask=mask.mask_data,
                        image_path=image_filename,
                        object_name=object_name
                    )
        
        # Export to JSON
        coco_dataset.export_to_json(output_path)
        return output_path
