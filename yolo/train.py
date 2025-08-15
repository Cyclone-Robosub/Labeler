from ultralytics import YOLO

# Load a model
model = YOLO("yolo11n.pt")  # load a pretrained model (recommended for training)

# Train using the single most idle GPU
results = model.train(
    data="/home/kid/roboSub/Labeler/yolo/data.yaml", 
    epochs=300,
    patience=30,

    device="cuda",
    project="RoboSub_gate",
    # save_period=10,

    augment=True,
    )