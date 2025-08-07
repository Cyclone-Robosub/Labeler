"""
Pure data models for the video labeling application
These models contain no UI or business logic dependencies
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np


@dataclass
class Point:
    """Represents a point annotation"""
    x: int
    y: int
    label: int  # 1 for positive, 0 for negative
    frame_index: int


@dataclass
class Mask:
    """Represents a segmentation mask"""
    mask_data: np.ndarray
    object_id: int
    frame_index: int
    confidence: float = 1.0


@dataclass
class VideoInfo:
    """Video metadata and properties"""
    path: str
    width: int = 0
    height: int = 0
    fps: float = 0.0
    total_frames: int = 0
    duration: float = 0.0
    
    @property
    def resolution_string(self) -> str:
        return f"{self.width}x{self.height}"


@dataclass
class AnnotationSession:
    """Represents an annotation session"""
    video_info: VideoInfo
    start_frame: int = 0
    current_frame: int = 0
    points: List[Point] = field(default_factory=list)
    masks: Dict[int, Dict[int, Mask]] = field(default_factory=dict)  # frame_index -> object_id -> mask
    frame_paths: List[str] = field(default_factory=list)  # Paths to extracted frame files
    is_initialized: bool = False
    
    def add_point(self, point: Point):
        """Add a point annotation"""
        self.points.append(point)
    
    def add_mask(self, mask: Mask):
        """Add a mask for a specific frame and object"""
        if mask.frame_index not in self.masks:
            self.masks[mask.frame_index] = {}
        self.masks[mask.frame_index][mask.object_id] = mask
    
    def get_masks_for_frame(self, frame_index: int) -> Dict[int, Mask]:
        """Get all masks for a specific frame"""
        return self.masks.get(frame_index, {})
    
    def get_points_for_frame(self, frame_index: int) -> List[Point]:
        """Get all points for a specific frame"""
        return [p for p in self.points if p.frame_index == frame_index]


@dataclass
class ApplicationState:
    """Overall application state"""
    current_session: Optional[AnnotationSession] = None
    is_playing: bool = False
    is_processing: bool = False
    status_message: str = "Ready"
    
    @property
    def has_video(self) -> bool:
        return self.current_session is not None
    
    @property
    def has_annotations(self) -> bool:
        return (self.current_session is not None and 
                (len(self.current_session.points) > 0 or len(self.current_session.masks) > 0))
