"""
Pure data models for the video labeling application
These models contain no UI or business logic dependencies
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np


@dataclass
class ObjectDefinition:
    """Represents an object type that can be annotated"""
    id: int
    name: str
    color: Tuple[int, int, int] = (255, 0, 0)  # BGR color for visualization
    
    def __post_init__(self):
        """Ensure we have a valid color tuple"""
        if not isinstance(self.color, tuple) or len(self.color) != 3:
            self.color = (255, 0, 0)  # Default to blue


@dataclass
class Point:
    """Represents a point annotation"""
    x: int
    y: int
    label: int  # 1 for positive, 0 for negative
    frame_index: int
    object_id: int = 1  # Which object this point belongs to


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
    needs_propagation: bool = False  # Flag to indicate if propagation is needed
    
    # Multi-object support
    objects: Dict[int, ObjectDefinition] = field(default_factory=dict)  # object_id -> ObjectDefinition
    current_object_id: Optional[int] = None  # Currently selected object for annotation
    next_object_id: int = 1  # Auto-incrementing object ID counter
    
    def add_object(self, name: str, color: Optional[Tuple[int, int, int]] = None) -> ObjectDefinition:
        """Add a new object definition and return it"""
        if color is None:
            # Generate a color based on object ID
            colors = [
                (255, 0, 0),    # Blue
                (0, 255, 0),    # Green  
                (0, 0, 255),    # Red
                (255, 255, 0),  # Cyan
                (255, 0, 255),  # Magenta
                (0, 255, 255),  # Yellow
                (128, 0, 128),  # Purple
                (255, 165, 0),  # Orange
            ]
            color = colors[self.next_object_id % len(colors)]
        
        obj_def = ObjectDefinition(id=self.next_object_id, name=name, color=color)
        self.objects[self.next_object_id] = obj_def
        
        # Set as current object if it's the first one
        if self.current_object_id is None:
            self.current_object_id = self.next_object_id
        
        self.next_object_id += 1
        return obj_def
    
    def get_current_object(self) -> Optional[ObjectDefinition]:
        """Get the currently selected object definition"""
        if self.current_object_id is None:
            return None
        return self.objects.get(self.current_object_id)
    
    def set_current_object(self, object_id: int):
        """Set the current object for annotation"""
        if object_id in self.objects:
            self.current_object_id = object_id
    
    def add_point(self, point: Point):
        """Add a point annotation"""
        self.points.append(point)
    
    def remove_last_point(self) -> Optional[Point]:
        """Remove and return the last point annotation"""
        if self.points:
            return self.points.pop()
        return None
    
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
    
    def get_points_for_object_on_frame(self, frame_index: int, object_id: int) -> List[Point]:
        """Get all points for a specific object on a specific frame"""
        return [p for p in self.points 
                if p.frame_index == frame_index and p.object_id == object_id]
    
    def get_all_points_for_current_object_on_frame(self, frame_index: int) -> List[Point]:
        """Get all points for the current object on a specific frame"""
        if self.current_object_id is None:
            return []
        return self.get_points_for_object_on_frame(frame_index, self.current_object_id)


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
