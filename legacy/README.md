# Legacy Implementation

This folder contains the original implementation before the MVVM refactoring.

## Files
- `view.py` - Original OpenCV-based UI
- `viewModel.py` - Mixed UI and business logic (not true MVVM)
- `coco_visualization.py` - COCO visualization utilities
- `convert_coco_yolo.py` - Format conversion tools

## Why These Were Refactored

### Problems with Original Design
1. **Tight Coupling**: UI and business logic mixed together
2. **Hard to Test**: No way to test logic without UI
3. **Not Extensible**: Adding new UI would require code duplication
4. **OpenCV Dependency**: UI tied to specific graphics library

### MVVM Solution
The new implementation in `src/` provides:
- Clean separation of concerns
- Testable business logic
- UI-agnostic services
- Future-proof architecture

## Migration Guide
If you need to use legacy code:
```python
# Old way
from legacy.viewModel import BlockLabeler
labeler = BlockLabeler("video.mp4")

# New way  
from src.mvvm.viewmodel import VideoLabelerViewModel
viewmodel = VideoLabelerViewModel()
viewmodel.load_video_command.execute("video.mp4")
```

These files are kept for reference and comparison purposes.
