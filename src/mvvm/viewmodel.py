"""
ViewModel layer - Contains presentation logic and coordinates between Model and View
This ViewModel is UI-agnostic and can work with different frontend technologies
"""
import os
from typing import Optional, List, Dict, Callable
import numpy as np
import cv2

from .observable import Observable, ObservableProperty, Command
from .models import VideoInfo, Point, Mask, AnnotationSession, ApplicationState, ObjectDefinition
from .services import VideoService, AnnotationService, ExportService


class VideoLabelerViewModel(Observable):
    """
    Main ViewModel for the video labeling application
    Contains all presentation logic without UI dependencies
    """
    
    # Observable properties that UI can bind to
    current_frame_index = ObservableProperty(0)
    is_playing = ObservableProperty(False)
    is_processing = ObservableProperty(False)
    status_message = ObservableProperty("Ready")
    
    def __init__(self):
        super().__init__()
        
        # Services (dependency injection ready)
        self.video_service = VideoService()
        self.annotation_service = AnnotationService()
        self.export_service = ExportService()
        
        # Application state
        self.app_state = ApplicationState()
        self.current_session: Optional[AnnotationSession] = None
        
        # UI-agnostic commands
        self.load_video_command = Command(self._load_video)
        self.play_pause_command = Command(self._toggle_play_pause, self._can_play_pause)
        self.next_frame_command = Command(self._next_frame, self._has_video)
        self.previous_frame_command = Command(self._previous_frame, self._has_video)
        self.jump_to_frame_command = Command(self._jump_to_frame, self._has_video)
        self.add_point_command = Command(self._add_point, self._can_add_point)
        self.undo_point_command = Command(self._undo_last_point, self._can_undo_point)
        self.add_object_command = Command(self._add_object, self._has_video)
        self.select_object_command = Command(self._select_object, self._has_objects)
        self.propagate_command = Command(self._propagate_annotations, self._can_propagate)
        self.export_coco_command = Command(self._export_coco, self._has_annotations)
        self.export_coco_partial_command = Command(self._export_coco_partial, self._has_annotations)
        
        # Current frame data
        self._current_frame: Optional[np.ndarray] = None
        self._current_frame_with_overlay: Optional[np.ndarray] = None
    
    # Properties for UI binding
    @property
    def video_info(self) -> Optional[VideoInfo]:
        return self.current_session.video_info if self.current_session else None
    
    @property
    def total_frames(self) -> int:
        return self.video_info.total_frames if self.video_info else 0
    
    @property
    def current_time(self) -> float:
        if not self.video_info or self.video_info.fps == 0:
            return 0.0
        return self.current_frame_index / self.video_info.fps
    
    @property
    def has_video(self) -> bool:
        return self.current_session is not None
    
    @property
    def has_annotations(self) -> bool:
        return (self.current_session is not None and 
                (len(self.current_session.points) > 0 or len(self.current_session.masks) > 0))
    
    @property
    def needs_propagation(self) -> bool:
        return (self.current_session is not None and 
                self.current_session.needs_propagation)
    
    @property
    def available_objects(self) -> Dict[int, 'ObjectDefinition']:
        """Get all available object definitions"""
        if not self.current_session:
            return {}
        return self.current_session.objects
    
    @property
    def current_object(self) -> Optional['ObjectDefinition']:
        """Get the currently selected object"""
        if not self.current_session:
            return None
        return self.current_session.get_current_object()
    
    @property
    def current_object_name(self) -> str:
        """Get the name of the currently selected object"""
        obj = self.current_object
        return obj.name if obj else "No object selected"
    
    @property
    def current_frame_points(self) -> List[Point]:
        if not self.current_session:
            return []
        return self.current_session.get_points_for_frame(self.current_frame_index)
    
    @property
    def current_frame_masks(self) -> Dict[int, Mask]:
        if not self.current_session:
            return {}
        return self.current_session.get_masks_for_frame(self.current_frame_index)
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get current frame data for display"""
        if not self.has_video:
            return None
        
        if self._current_frame is None:
            self._current_frame = self.video_service.get_frame(self.current_frame_index)
        
        return self._current_frame
    
    def get_current_frame_with_overlay(self) -> Optional[np.ndarray]:
        """Get current frame with annotations overlay"""
        base_frame = self.get_current_frame()
        if base_frame is None:
            return None
        
        # Create a copy for overlay
        frame_with_overlay = base_frame.copy()
        
        # Add masks overlay
        for obj_id, mask in self.current_frame_masks.items():
            frame_with_overlay = self._draw_mask_overlay(frame_with_overlay, mask.mask_data, obj_id)
        
        # Add points overlay
        for point in self.current_frame_points:
            frame_with_overlay = self._draw_point_overlay(frame_with_overlay, point)
        
        return frame_with_overlay
    
    # Command implementations
    def _load_video(self, video_path: str):
        """Load a video file, preserving object classes if they exist"""
        try:
            self.status_message = "Loading video..."
            
            # Preserve existing object definitions if we have a current session
            existing_objects = {}
            current_object_id = None
            next_object_id = 1
            
            if self.current_session:
                existing_objects = self.current_session.objects.copy()
                current_object_id = self.current_session.current_object_id
                next_object_id = self.current_session.next_object_id
                self.status_message = "Loading video (preserving objects)..."
            
            # Load new video
            video_info = self.video_service.load_video(video_path)
            
            # Create new annotation session
            self.current_session = AnnotationSession(video_info=video_info)
            
            # Restore object definitions if they existed
            if existing_objects:
                self.current_session.objects = existing_objects
                self.current_session.current_object_id = current_object_id
                self.current_session.next_object_id = next_object_id
                self.status_message = f"Video loaded: {os.path.basename(video_path)} (objects preserved)"
            else:
                self.status_message = f"Video loaded: {os.path.basename(video_path)}"
            
            self.current_frame_index = 0
            self._current_frame = None
            
            self.notify_observers("video_loaded", None, video_info)
            
        except Exception as e:
            self.status_message = f"Error loading video: {str(e)}"
            raise
    
    def _toggle_play_pause(self):
        """Toggle play/pause state"""
        self.is_playing = not self.is_playing
        self.status_message = "Playing" if self.is_playing else "Paused"
    
    def _next_frame(self):
        """Advance to next frame"""
        if self.current_frame_index < self.total_frames - 1:
            # Check if we need to propagate before moving
            self._propagate_if_needed()
            
            self.current_frame_index += 1
            self._current_frame = None  # Force reload
    
    def _previous_frame(self):
        """Go to previous frame"""
        if self.current_frame_index > 0:
            # Check if we need to propagate before moving
            self._propagate_if_needed()
            
            self.current_frame_index -= 1
            self._current_frame = None  # Force reload
    
    def _jump_to_frame(self, frame_index: int):
        """Jump to specific frame"""
        frame_index = max(0, min(frame_index, self.total_frames - 1))
        if frame_index != self.current_frame_index:
            # Check if we need to propagate before moving
            self._propagate_if_needed()
            
            self.current_frame_index = frame_index
            self._current_frame = None  # Force reload
    
    def _add_point(self, x: int, y: int, label: int = 1):
        """Add a point annotation"""
        if not self.current_session:
            return
        
        # Check if an object is selected
        if self.current_session.current_object_id is None:
            self.status_message = "Please add and select an object first"
            return
        
        try:
            self.is_processing = True
            self.status_message = "Processing annotation..."
            
            # Check if this is the first annotation
            if not self.current_session.is_initialized:
                self._initialize_annotation_session()
            
            # Create point with absolute frame index and current object ID
            point = Point(
                x=x, y=y, label=label, 
                frame_index=self.current_frame_index,
                object_id=self.current_session.current_object_id
            )
            
            # Add to session
            self.current_session.add_point(point)
            
            # Calculate relative frame index for SAM2 (relative to annotation start)
            relative_frame_idx = self.current_frame_index - self.current_session.start_frame
            
            # Get all points for the current object on this frame
            all_points_for_object = self.current_session.get_all_points_for_current_object_on_frame(
                self.current_frame_index
            )
            
            # Convert to relative frame indices for SAM2
            relative_points = []
            for p in all_points_for_object:
                rel_frame_idx = p.frame_index - self.current_session.start_frame
                relative_points.append(Point(
                    x=p.x, y=p.y, label=p.label, 
                    frame_index=rel_frame_idx, object_id=p.object_id
                ))
            
            # Generate mask using annotation service with all points for this object
            mask = self.annotation_service.add_point_annotation(
                point=relative_points[-1],  # The new point (with relative frame index)
                all_points_for_object=relative_points
            )
            
            # Update mask to use absolute frame index for storage
            mask.frame_index = self.current_frame_index
            mask.object_id = self.current_session.current_object_id
            self.current_session.add_mask(mask)
            
            # Force UI update to show immediate mask result - this will trigger observers
            self._current_frame = None  # Force reload with overlay
            self.notify_observers("annotation_added", None, {"point": point, "mask": mask})
            
            point_type = "positive" if label == 1 else "negative"
            object_name = self.current_object_name
            self.status_message = f"Added {point_type} point for '{object_name}' at ({x}, {y})"
            
            # Mark that we need to propagate when frame changes
            self.current_session.needs_propagation = True
            
        except Exception as e:
            self.status_message = f"Error adding annotation: {str(e)}"
            raise
        finally:
            self.is_processing = False
    
    def _propagate_if_needed(self):
        """Propagate annotations through video if needed"""
        if not self.current_session or not self.current_session.needs_propagation:
            return
        
        try:
            self.is_processing = True
            self.status_message = "Propagating annotations through video..."
            
            # Run propagation through the entire video
            all_masks = self.annotation_service.propagate_annotations()
            
            # Update session with all masks, converting relative to absolute frame indices
            for relative_frame_idx, frame_masks in all_masks.items():
                absolute_frame_idx = self.current_session.start_frame + relative_frame_idx
                for obj_id, mask in frame_masks.items():
                    # Update mask to use absolute frame index
                    mask.frame_index = absolute_frame_idx
                    self.current_session.add_mask(mask)
            
            # Clear the propagation flag
            self.current_session.needs_propagation = False
            self.status_message = "Video propagation complete"
            
        except Exception as e:
            self.status_message = f"Error during propagation: {str(e)}"
            raise
        finally:
            self.is_processing = False
    
    def _initialize_annotation_session(self):
        """Initialize annotation session for SAM2"""
        if not self.current_session:
            return
        
        # Extract frames from current position to end
        video_name = os.path.basename(self.current_session.video_info.path).split('.')[0]
        frame_dir = os.path.join(video_name, "frames")
        
        self.status_message = "Extracting frames..."
        frame_paths = self.video_service.extract_frames_to_directory(
            self.current_frame_index, frame_dir
        )
        
        # Initialize annotation service (init_inference_state automatically resets)
        self.annotation_service.initialize_for_video(frame_dir)
        
        # Update session with frame paths and initialization status
        self.current_session.start_frame = self.current_frame_index
        self.current_session.frame_paths = frame_paths
        self.current_session.is_initialized = True
    
    def _propagate_annotations(self):
        """Manually trigger annotation propagation through video"""
        if not self.current_session:
            return
        
        # Force propagation even if not marked as needed
        self.current_session.needs_propagation = True
        self._propagate_if_needed()
    
    def _export_coco(self, output_path: str):
        """Export annotations in COCO format"""
        if not self.current_session:
            return
        
        try:
            self.status_message = "Exporting to COCO format..."
            self.export_service.export_to_coco(self.current_session, output_path)
            self.status_message = f"Exported to COCO format: {output_path}"
        except Exception as e:
            self.status_message = f"Error exporting to COCO: {str(e)}"
            raise
    
    def _export_coco_partial(self, output_path: str):
        """Export annotations in COCO format from start frame to current frame only"""
        if not self.current_session:
            return
        
        try:
            self.status_message = "Exporting partial annotations to COCO format..."
            # Convert current frame index to absolute frame index
            end_frame = self.current_session.start_frame + self.current_frame_index
            self.export_service.export_to_coco_partial(self.current_session, output_path, end_frame)
            self.status_message = f"Exported partial annotations to COCO format: {output_path}"
        except Exception as e:
            self.status_message = f"Error exporting partial COCO: {str(e)}"
            raise
    
    def _undo_last_point(self):
        """Undo the last point annotation"""
        if not self.current_session:
            return
        
        try:
            self.is_processing = True
            self.status_message = "Undoing last point..."
            
            # Remove the last point
            removed_point = self.current_session.remove_last_point()
            if not removed_point:
                self.status_message = "No points to undo"
                return
            
            # Get remaining points for the current object on this frame
            remaining_points = self.current_session.get_all_points_for_current_object_on_frame(
                self.current_frame_index
            )
            
            if remaining_points:
                # Re-generate mask with remaining points
                relative_frame_idx = self.current_frame_index - self.current_session.start_frame
                
                # Convert to relative frame indices for SAM2
                relative_points = []
                for p in remaining_points:
                    rel_frame_idx = p.frame_index - self.current_session.start_frame
                    relative_points.append(Point(
                        x=p.x, y=p.y, label=p.label, 
                        frame_index=rel_frame_idx, object_id=p.object_id
                    ))
                
                # Generate updated mask
                mask = self.annotation_service.add_point_annotation(
                    point=relative_points[-1],  # Use last remaining point as reference
                    all_points_for_object=relative_points
                )
                
                # Update mask to use absolute frame index for storage
                mask.frame_index = self.current_frame_index
                mask.object_id = self.current_session.current_object_id
                self.current_session.add_mask(mask)
            else:
                # No points left for this object on this frame - remove mask
                frame_masks = self.current_session.get_masks_for_frame(self.current_frame_index)
                if self.current_session.current_object_id in frame_masks:
                    del self.current_session.masks[self.current_frame_index][self.current_session.current_object_id]
            
            # Force UI update
            self._current_frame = None  # Force reload with overlay
            self.notify_observers("annotation_removed", None, {"removed_point": removed_point})
            
            point_type = "positive" if removed_point.label == 1 else "negative"
            self.status_message = f"Undone {point_type} point at ({removed_point.x}, {removed_point.y})"
            
            # Mark that we need to propagate when frame changes
            self.current_session.needs_propagation = True
            
        except Exception as e:
            self.status_message = f"Error undoing point: {str(e)}"
            raise
        finally:
            self.is_processing = False
    
    def _add_object(self, object_name: str):
        """Add a new object type for annotation"""
        if not self.current_session:
            return
        
        if not object_name or not object_name.strip():
            self.status_message = "Object name cannot be empty"
            return
        
        try:
            # Check if object name already exists
            for obj in self.current_session.objects.values():
                if obj.name.lower() == object_name.lower().strip():
                    self.status_message = f"Object '{object_name}' already exists"
                    return
            
            # Add new object
            new_object = self.current_session.add_object(object_name.strip())
            self.status_message = f"Added object '{new_object.name}' (ID: {new_object.id})"
            
            # Notify observers
            self.notify_observers("object_added", None, new_object)
            
        except Exception as e:
            self.status_message = f"Error adding object: {str(e)}"
            raise
    
    def _select_object(self, object_id: int):
        """Select an object for annotation"""
        if not self.current_session:
            return
        
        if object_id not in self.current_session.objects:
            self.status_message = f"Object ID {object_id} not found"
            return
        
        self.current_session.set_current_object(object_id)
        object_name = self.current_session.objects[object_id].name
        self.status_message = f"Selected object '{object_name}' for annotation"
        
        # Notify observers
        self.notify_observers("object_selected", None, {"object_id": object_id})
    
    # Command validation methods
    def _can_play_pause(self) -> bool:
        return self.has_video and not self.is_processing
    
    def _has_video(self) -> bool:
        return self.has_video and not self.is_processing
    
    def _can_add_point(self) -> bool:
        return (self.has_video and not self.is_processing and 
                self.current_session and self.current_session.current_object_id is not None)
    
    def _can_undo_point(self) -> bool:
        return (self.has_video and not self.is_processing and 
                self.current_session and len(self.current_session.points) > 0)
    
    def _has_objects(self) -> bool:
        return (self.has_video and not self.is_processing and 
                self.current_session and len(self.current_session.objects) > 0)
    
    def _can_propagate(self) -> bool:
        return (self.has_video and not self.is_processing and 
                self.current_session and self.current_session.is_initialized)
    
    def _has_annotations(self) -> bool:
        return self.has_annotations and not self.is_processing
    
    # Helper methods for visualization
    def _draw_mask_overlay(self, frame: np.ndarray, mask: np.ndarray, object_id: int, alpha: float = 0.6) -> np.ndarray:
        """Draw mask overlay on frame with object-specific color"""
        # Get object color
        color = (255, 0, 0)  # Default blue
        if self.current_session and object_id in self.current_session.objects:
            color = self.current_session.objects[object_id].color
        
        colored_mask = np.zeros_like(frame, dtype=np.uint8)
        mask = np.squeeze(mask)
        colored_mask[mask > 0] = color
        return cv2.addWeighted(frame, 1.0, colored_mask, alpha, 0)
    
    def _draw_point_overlay(self, frame: np.ndarray, point: Point, marker_size: int = 8) -> np.ndarray:
        """Draw point overlay on frame"""
        color = (0, 255, 0) if point.label == 1 else (0, 0, 255)  # Green for positive, Red for negative
        cv2.drawMarker(frame, (point.x, point.y), color, cv2.MARKER_STAR, 
                      markerSize=marker_size, thickness=2)
        # White border
        cv2.drawMarker(frame, (point.x, point.y), (255, 255, 255), cv2.MARKER_STAR, 
                      markerSize=marker_size, thickness=1)
        return frame
    
    def cleanup(self):
        """Clean up resources"""
        self.video_service.cleanup()
        self.current_session = None
        self._current_frame = None
