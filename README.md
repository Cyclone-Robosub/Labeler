### labeling pipeline
#### Step 0: Prerequisites
Install [SAM2](https://github.com/facebookresearch/sam2) first. And download the [sam2.1_hiera_large.pt](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt) to sam2_checkpoint folder. 
Then install the requirements by running:
```bash
pip install -r requirements.txt
```

#### Step 1: Label the blocks
```bash
python run_labeler.py
```