from ultralytics import YOLO

model = YOLO("/home/kid/roboSub/Labeler/RoboSub/train/weights/last.pt")

model.predict(source="/media/kid/128/Movie on 7-27-25 at 2.18 PM.mov", show=True)