# take the video file path
# reverse the video
# play the video frame by frame
  # ask for point prompt each frame
  # (get the prompt) extract each frame into a folder
# use SAM2 to track the video with the prompt
# (visualize the tracking)
# output the annotation in coco format

import os
# if using Apple MPS, fall back to CPU for unsupported ops
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
import numpy as np
import torch
from PIL import Image
from sam2.build_sam import build_sam2_video_predictor


class Labeler:

    video_segments = {}  # video_segments contains the per-frame segmentation results
    # map[frame_idx] = mask

    def __init__(self, model_path):
        # select the device for computation
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")
        print(f"using device: {device}")

        if device.type == "cuda":
            # use bfloat16 for the entire notebook
            torch.autocast("cuda", dtype=torch.bfloat16).__enter__()
            # turn on tfloat32 for Ampere GPUs (https://pytorch.org/docs/stable/notes/cuda.html#tensorfloat-32-tf32-on-ampere-devices)
            if torch.cuda.get_device_properties(0).major >= 8:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
        elif device.type == "mps":
            print(
                "\nSupport for MPS devices is preliminary. SAM 2 is trained with CUDA and might "
                "give numerically different outputs and sometimes degraded performance on MPS. "
                "See e.g. https://github.com/pytorch/pytorch/issues/84936 for a discussion."
            )


        sam2_checkpoint = model_path
        model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"

        self.predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint, device=device)

    def init_inference_state(self, video_dir):
        self.inference_state = self.predictor.init_state(video_path=video_dir)

    def select_objects(self, points, labels, ann_obj_id, ann_frame_idx=0):

        _, out_obj_ids, out_mask_logits = self.predictor.add_new_points_or_box(
            inference_state=self.inference_state,
            frame_idx=ann_frame_idx,
            obj_id=ann_obj_id,
            points=points,
            labels=labels,
        )

        return out_obj_ids, (out_mask_logits[0] > 0.0).cpu().numpy()
    
    def run_through_video(self):
        self.video_segments = {}
        for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(self.inference_state):
            self.video_segments[out_frame_idx] = {
                out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
                for i, out_obj_id in enumerate(out_obj_ids)
            }

