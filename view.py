import cv2
import numpy as np
from viewModel import BlockLabeler
import argparse



parser = argparse.ArgumentParser(description="Block Detection Video Labeler")
parser.add_argument("video_path", type=str, help="Path to the video file")
args = parser.parse_args()

video_path = args.video_path

block_labeler = BlockLabeler(video_path)

cv2.namedWindow('Frame by Frame Player', cv2.WINDOW_AUTOSIZE)
cv2.setMouseCallback('Frame by Frame Player', block_labeler.mouse_callback)

print("\nControls:")
print("  'd' or SPACE: Next frame")
print("  'q': Quit")
print("  'r': Reset to beginning")
print("  'a': Previous frame")
print("  'j': Jump to frame (enter number)")
print("  Click: label point")

while not block_labeler.quit_video:
    frame = block_labeler.show_frame()
    
    
    # Frame info
    cv2.putText(frame, f"Frame: {block_labeler.current_frame_index}/{block_labeler.total_frames}", 
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Time: {(block_labeler.current_frame_index/block_labeler.fps):.2f}s", 
                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.imshow('Frame by Frame Player', frame)
    
    # Handle input
    key = cv2.waitKey(1) & 0xFF
    block_labeler.handle_key(key)
    

block_labeler.cap.release()
cv2.destroyAllWindows()


# make this a loop keep running until quit or finished
# keep showing what view model have
# allow forward and backward and left and right clicks
# create and adjust the masks
