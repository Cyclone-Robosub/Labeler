# Video Labeler - MVVM Edition

A professional video annotation tool built with clean MVVM architecture, featuring SAM2 integration for intelligent object segmentation.

## 🚀 Features

- **MVVM Architecture**: Clean separation of concerns for maintainable code
- **SAM2 Integration**: State-of-the-art object segmentation and tracking
- **Real-time Visualization**: Interactive mask overlay and point annotations
- **COCO Export**: Standard format for machine learning workflows
- **Future-Ready**: Designed for easy web/mobile deployment

## 📁 Project Structure

```
video-labeler/
├── src/                          # Source code
│   ├── labeler/                  # Core labeling functionality
│   │   ├── model.py              # SAM2 integration
│   │   └── dataset.py            # COCO dataset handling
│   ├── mvvm/                     # MVVM architecture
│   │   ├── models.py             # Data models
│   │   ├── viewmodel.py          # Presentation logic
│   │   ├── services.py           # Business services
│   │   └── observable.py         # Data binding system
│   ├── ui/                       # User interface
│   │   └── tkinter_view.py       # Desktop UI (tkinter)
│   └── app.py                    # Main application
├── legacy/                       # Original implementation
├── examples/                     # Sample outputs and demos
├── docs/                         # Documentation
├── yolo/                         # YOLO training scripts
├── sam2_checkpoint/              # SAM2 model files
└── run_labeler.py               # Application launcher
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd video-labeler
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download SAM2 model** (if not present)
   ```bash
   # Download sam2.1_hiera_large.pt to sam2_checkpoint/
   ```

## 🎮 Usage

### Quick Start
```bash
python3 run_labeler.py
```

### Controls
- **Left click**: Add positive point annotation
- **Right click**: Add negative point annotation  
- **← → arrows**: Navigate frames
- **Space**: Next frame
- **File menu**: Open video, save annotations

### Workflow
1. **Open Video**: File → Open Video...
2. **Navigate**: Use arrow keys or buttons to find your target
3. **Annotate**: Click on the object to start tracking
4. **Refine**: Add positive/negative points as needed
5. **Export**: File → Export COCO... to save annotations

## 🏗️ Architecture

### MVVM Benefits
- **Testable**: Business logic separated from UI
- **Maintainable**: Clear separation of concerns  
- **Extensible**: Easy to add new UI frontends
- **Reusable**: Services work across different interfaces

### Key Components

#### Models (`src/mvvm/models.py`)
Pure data classes with no dependencies:
- `VideoInfo`: Video metadata
- `Point`: Point annotations
- `Mask`: Segmentation masks
- `AnnotationSession`: Session state

#### Services (`src/mvvm/services.py`)
UI-agnostic business logic:
- `VideoService`: Video file operations
- `AnnotationService`: SAM2 integration
- `ExportService`: COCO format export

#### ViewModel (`src/mvvm/viewmodel.py`)
Presentation logic coordinator:
- Observable properties for data binding
- Command pattern for user actions
- No UI dependencies

#### View (`src/ui/tkinter_view.py`)
Pure UI layer:
- Data binding to ViewModel
- Event handling
- Visual rendering

## 📊 Output Format

Annotations are exported in COCO format:
```json
{
  "images": [...],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 1,
      "bbox": [x, y, width, height],
      "area": 1234,
      "segmentation": {...}
    }
  ],
  "categories": [...]
}
```

## 🔮 Future Development

The MVVM architecture enables easy expansion:

### Planned Features
- **Web Interface**: FastAPI + WebSocket + HTML5 Canvas
- **Mobile Support**: Progressive Web App
- **Multi-user**: Real-time collaboration
- **Cloud Deployment**: Docker + Kubernetes ready

### Adding New UI Frontends
The ViewModel is UI-agnostic, making it easy to add:
- Web browser interface
- Mobile app
- Jupyter notebook widget
- VS Code extension

## 🧪 Development

### Running Tests
```bash
# Unit tests for business logic
python -m pytest tests/

# Test ViewModel without UI
python -m pytest tests/test_viewmodel.py
```

### Adding Features
1. **Models**: Add data structures in `models.py`
2. **Services**: Add business logic in `services.py`  
3. **ViewModel**: Add presentation logic in `viewmodel.py`
4. **View**: Add UI in appropriate view file

## 📝 License

[Add your license here]

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For questions and support:
- Create an issue on GitHub
- Check the documentation in `docs/`
- Review example outputs in `examples/`
