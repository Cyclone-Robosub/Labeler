from ultralytics import YOLO

# Load a model
model = YOLO("yolo11n.pt")  # load a pretrained model (recommended for training)

# Train using the single most idle GPU
results = model.train(data="/home/kid/roboSub/Labeler/data.yaml", 
    epochs=100, 
    imgsz=640, 
    device="cuda",
    project="RoboSub",
    save_period=10,

    augment=True,
    )