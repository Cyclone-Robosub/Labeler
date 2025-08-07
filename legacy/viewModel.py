import cv2
import os
import numpy as np

# from view import get_click_on_frame, visualize_sam2_results
from model import Labeler
from dataset import COCODataset

def draw_mask(frame, mask, obj_id=None, random_color=False, alpha=0.6):
    """
    Draw mask overlay on OpenCV frame with blue color only

    Args:
        frame: OpenCV image (BGR format)
        mask: Binary mask array
        obj_id: (ignored)
        random_color: (ignored)
        alpha: Transparency of the mask overlay

    Returns:
        frame: Modified frame with blue mask overlay
    """
    color = (255, 0, 0)  # Blue in BGR
    colored_mask = np.zeros_like(frame, dtype=np.uint8)
    mask = np.squeeze(mask)
    colored_mask[mask > 0] = color
    cv2.addWeighted(frame, 1.0, colored_mask, alpha, 0, frame)
    return frame


def draw_points(frame, coords, labels, marker_size=8, thickness=2):
    """
    Draw points on OpenCV frame
    
    Args:
        frame: OpenCV image (BGR format)
        coords: Array of point coordinates [[x, y], ...]
        labels: Array of point labels (1 for positive, 0 for negative)
        marker_size: Size of the point markers
        thickness: Thickness of the point markers
    
    Returns:
        frame: Modified frame with points drawn
    """
    for coord, label in zip(coords, labels):
        x, y = int(coord[0]), int(coord[1])
        
        if label == 1:  # Positive point
            # Draw green star-like marker
            cv2.drawMarker(frame, (x, y), (0, 255, 0), cv2.MARKER_STAR, 
                          markerSize=marker_size, thickness=thickness)
            # Add white border
            cv2.drawMarker(frame, (x, y), (255, 255, 255), cv2.MARKER_STAR, 
                          markerSize=marker_size, thickness=1)
        else:  # Negative point
            # Draw red star-like marker
            cv2.drawMarker(frame, (x, y), (0, 0, 255), cv2.MARKER_STAR, 
                          markerSize=marker_size, thickness=thickness)
            # Add white border
            cv2.drawMarker(frame, (x, y), (255, 255, 255), cv2.MARKER_STAR, 
                          markerSize=marker_size, thickness=1)
    
    return frame


def draw_box(frame, box, color=(0, 255, 0), thickness=2):
    """
    Draw bounding box on OpenCV frame
    
    Args:
        frame: OpenCV image (BGR format)
        box: Bounding box coordinates [x_min, y_min, x_max, y_max]
        color: Box color in BGR format
        thickness: Box line thickness
    
    Returns:
        frame: Modified frame with bounding box drawn
    """
    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    
    return frame


def visualize_sam2_results(frame, masks_dict, points=None, labels=None, boxes=None):
    """
    Comprehensive visualization function for SAM2 results
    
    Args:
        frame: OpenCV image (BGR format)
        masks_dict: Dictionary with obj_id as key and mask as value
        points: Point coordinates (optional)
        labels: Point labels (optional)
        boxes: List of bounding boxes (optional)
    
    Returns:
        frame: Annotated frame
    """
    # Draw masks
    if masks_dict:
        for obj_id, mask in masks_dict.items():
            frame = draw_mask(frame, mask, obj_id=obj_id)
    
    # Draw points
    if points is not None and labels is not None:
        frame = draw_points(frame, points, labels)
    
    # Draw boxes
    if boxes is not None:
        for box in boxes:
            frame = draw_box(frame, box)
    
    return frame



class BlockLabeler:
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.quit_video = False
        self.paused = False
        self.current_frame_index = 0
        self.labeler = None
        self.anno_start_idx = None
        self.current_frame = None
        self.video_name = os.path.basename(video_path).split('.')[0]

        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Video loaded: {os.path.basename(video_path)}")
        print(f"Resolution: {self.width}x{self.height}")
        print(f"FPS: {self.fps:.2f}")
        print(f"Total frames: {self.total_frames}")
        print(f"Duration: {self.total_frames/self.fps:.2f} seconds")

    def show_frame(self):
        if self.current_frame is None:
            self.update_frame(self.current_frame_index)

        return self.current_frame


    def set_frame(self):
        """Get the next frame from the video"""
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_index)
        _, frame = self.cap.read()

        if self.anno_start_idx is not None and len(self.labeler.video_segments) > 0:
            # Annotate the frame with the current labeler state
            masks_dict = self.labeler.video_segments[self.current_frame_index - self.anno_start_idx]
            frame = visualize_sam2_results(frame, masks_dict)
        
        self.current_frame = frame

    def reset_frame(self):

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_index)
        self.current_frame = self.cap.read()[1]
        
    
    def extract_frames_from_curr_to_end(self):
        self.anno_start_idx = self.current_frame_index
        print(f"Extracting frames from {self.anno_start_idx} to end of video...")

        # Create a temporary directory to store frames
        self.frame_dir = self.video_name + "/frames/"
        os.makedirs(self.frame_dir, exist_ok=True)
        # remove existing frames
        for f in os.listdir(self.frame_dir):
            os.remove(os.path.join(self.frame_dir, f))

        frame_idx = self.current_frame_index
        while frame_idx < self.total_frames:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            frame = self.cap.read()[1]
                
            # Save frame with 5-digit zero-padded filename
            frame_filename = os.path.join(self.frame_dir, f"{frame_idx:05d}.jpg")

            # Save with specified quality
            cv2.imwrite(frame_filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
            frame_idx += 1

        self.frame_names = [
            p for p in os.listdir(self.frame_dir)
            if os.path.splitext(p)[-1] in [".jpg", ".jpeg", ".JPG", ".JPEG"]
        ]
        self.frame_names.sort(key=lambda p: int(os.path.splitext(p)[0]))

    def init_labeler(self):
        """Initialize the Labeler with the current video"""
        self.labeler = Labeler("sam2_checkpoint/sam2.1_hiera_large.pt")
        self.labeler.init_inference_state(video_dir=self.frame_dir)
        print("Labeler initialized with video frames.")

    def draw_selected_object(self, x, y, label):
        _, mask = self.labeler.select_objects(
                points=np.array([[x, y]]),
                labels=np.array([label], np.int32),
                ann_obj_id=1,
                ann_frame_idx=self.current_frame_index - self.anno_start_idx
            )

        # update the showing frame
        self.reset_frame() # reset the current frame
        self.current_frame = draw_mask(self.current_frame, mask)
        self.current_frame = draw_points(self.current_frame, np.array([[x, y]]), np.array([label]), 10)

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f"Click at ({x}, {y}) - Frame {self.current_frame_index + 1}")

            self.paused = True

            if self.labeler is None: # first click
                self.extract_frames_from_curr_to_end()
                self.init_labeler()
                self.draw_selected_object(x, y, 1)

                # may ask for additional confirmation before running through the video
                self.labeler.run_through_video()

            else: 
                # Add a new point to the current frame
                self.draw_selected_object(x, y, 1)
                self.labeler.run_through_video()

            self.paused = False
        elif event == cv2.EVENT_RBUTTONDOWN:
            print(f"Right click at ({x}, {y}) - Frame {self.current_frame_index + 1}")

            # assume labeler is initialized
            self.paused = True
            self.draw_selected_object(x, y, 0)
            self.labeler.run_through_video()
            self.paused = False


        elif event == cv2.EVENT_RBUTTONDOWN:
            self.paused = not self.paused
            print(f"Right click - {'Paused' if self.paused else 'Playing'}")

    def update_frame(self, idx):
        if self.current_frame_index == idx and self.current_frame is not None:
            return
        
        self.current_frame_index = idx
        self.set_frame()

    def jump_to_frame(self, frame_num):
        """Jump to a specific frame number"""
        frame_num = max(0, min(frame_num, self.total_frames - 1))
        self.update_frame(frame_num)

    def advance_frame(self):
        """Advance to the next frame"""
        if self.current_frame_index < self.total_frames - 1:
            self.update_frame(self.current_frame_index + 1)
        else:
            print("Already at the last frame")

    def rewind_frame(self):
        """Rewind to the previous frame"""
        if self.current_frame_index > 0:
            self.update_frame(self.current_frame_index - 1)
        else:
            print("Already at the first frame")

    def handle_key(self, key):
        if self.paused:
            # work as a blocker
            print("waiting for processing to finish...")
            return

        if key == ord('q'):
            self.quit_video = True
        elif key == ord(' '):
            self.advance_frame()
        elif key == ord('r'):
            self.jump_to_frame(0)
        elif key == ord('d'):
            self.advance_frame()
        elif key == ord('a'):
            self.rewind_frame()
        elif key == ord('s'):
            # save frames from anno_start_idx to current_frame_index
            self.save_labels(0, self.current_frame_index - self.anno_start_idx)
        elif key == ord('j'):
            frame_num = input("Enter frame number: ")
            try:
                self.jump_to_frame(int(frame_num) - 1)
            except ValueError:
                print("Invalid frame number")

    def save_labels(self, start_idx, end_idx):
        block_dataset = COCODataset("block_detection_dataset", "block")
        
        # make each file name unique, prefix with video name

        # rename the files in the images directory
        for i in range(len(self.frame_names)):
            old_name = os.path.join(self.frame_dir, self.frame_names[i])
            new_name = os.path.join(self.frame_dir, f"{self.video_name}_{self.frame_names[i]}")
            os.rename(old_name, new_name)
            self.frame_names[i] = new_name
        

        for i in range(start_idx, end_idx + 1):
            block_dataset.add_sam_mask(
                mask=self.labeler.video_segments[i][1],  # Assuming obj_id 1 for the block
                image_path=self.frame_names[i]
            )

        block_dataset.export_to_json(os.path.join(self.video_name, "labels.json"))
