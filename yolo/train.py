from ultralytics import YOLO

# Load a model
model = YOLO("/home/kid/roboSub/Labeler/july_27_best.pt")  # load a pretrained model (recommended for training)

# Train using the single most idle GPU
results = model.train(
    data="/home/kid/roboSub/Labeler/data.yaml", 
    epochs=300,
    patience=30,

    imgsz=512,
    batch=128,

    device="cuda",
    project="Block detector",
    # save_period=10,

    augment=True,
    )