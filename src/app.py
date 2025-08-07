#!/usr/bin/env python3
"""
Main application entry point for the Video Labeler
MVVM Architecture with tkinter UI
"""

from .ui.tkinter_view import VideoLabelerApp

def main():
    """Main entry point for the MVVM Video Labeler"""
    print("🎬 Video Labeler - MVVM Edition")
    print("=" * 40)
    print("\n✨ Features:")
    print("  • MVVM architecture for clean separation of concerns")
    print("  • SAM2 integration for intelligent object segmentation") 
    print("  • Real-time mask overlay and point visualization")
    print("  • COCO format export for ML workflows")
    print("  • Future-ready for web deployment")
    
    print("\n🎮 Controls:")
    print("  • Left click: Add positive point annotation")
    print("  • Right click: Add negative point annotation") 
    print("  • ← → arrows: Navigate frames")
    print("  • Space: Next frame")
    print("  • File menu: Open video, save annotations")
    
    print("\n🚀 Starting application...")
    
    # Start the application
    app = VideoLabelerApp()
    app.run()

if __name__ == "__main__":
    main()
