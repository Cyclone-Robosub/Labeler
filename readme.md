### labeling pipeline
#### Step 0: Prerequisites
Install [SAM2](https://github.com/facebookresearch/sam2) first.

##### Example
```bash
Box and Blocks_ZHAE_Affected_FU_attempts % ffmpeg -i Box\ and\ Blocks_ZHAE_Affected_FU_0.mp4 -vf reverse -af areverse Box\ and\ Blocks_ZHAE_Affected_FU_0_reversed.mp4
```

#### Step 1: Label the blocks
Back to this directory, you can run `python view.py` to start the labeling process. The script will load the reversed videos and allow you to label the blocks by drawing bounding boxes around them. The labeled frames will be saved in the `images/` directory. Once you finished labeling, you can press `s` to save the labels. The labels will be saved in a JSON file named `labels.json`.

##### Usage
- `d` - forward one frame
- `a` - backward one frame
- `Left Click` - provides a positive prompt. A point to tell SAM where the block is.
- `Right Click` - provides a negative prompt. A point to adjust the mask on where it is not a block. However, the negative prompt doesn't prove to be very helpful in practice.... 
- `s` - save labels from first positive click **To the current frame**, this way you can discard the frames when SAM fails to track the blocks. It also generates a JSON file with the labels.
- `j` - jump to a specific frame number
- `r` - rewind to the first frame
- `q` - quit the labeling process

##### Becareful on your first click
The first click should be positive and once you click, you cannot include any frame before it.

##### Example
```bash
block_detection % python view.py robovid.mp4
```

#### Optional Step 4: check the labels
install fiftyone by `pip install fiftyone`. (I would suggest you create a virtual environment for this)
Run `python coco_visualization.py images/ labels.json` to visualize the labels you just created. This will open up a brower tab on port `5151`.
