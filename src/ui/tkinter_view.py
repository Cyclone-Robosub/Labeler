"""
Tkinter View layer for the video labeling application
This handles all UI rendering and user input, binding to the ViewModel
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import cv2
from typing import Optional
import os

from ..mvvm.viewmodel import VideoLabelerViewModel


class VideoCanvas(tk.Canvas):
    """Custom canvas for video display with mouse interaction"""
    
    def __init__(self, parent, viewmodel: VideoLabelerViewModel, **kwargs):
        super().__init__(parent, bg='black', **kwargs)
        self.viewmodel = viewmodel
        self.current_image = None
        self.photo_image = None
        
        # Bind mouse events
        self.bind("<Button-1>", self._on_left_click)
        self.bind("<Button-3>", self._on_right_click)
        
        # Listen to viewmodel changes
        self.viewmodel.add_observer("current_frame_index", self._on_frame_changed)
    
    def update_frame(self, frame: Optional[np.ndarray]):
        """Update the canvas with a new frame"""
        if frame is None:
            self.delete("all")
            return
        
        # Convert BGR to RGB for PIL
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        
        # Resize to fit canvas while maintaining aspect ratio
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:  # Canvas is initialized
            # Calculate scaling to fit canvas
            img_width, img_height = pil_image.size
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            scale = min(scale_x, scale_y)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage for tkinter
        self.photo_image = ImageTk.PhotoImage(pil_image)
        
        # Clear canvas and add image
        self.delete("all")
        self.create_image(
            canvas_width // 2, canvas_height // 2,
            image=self.photo_image,
            anchor=tk.CENTER
        )
        
        self.current_image = pil_image
    
    def _on_left_click(self, event):
        """Handle left mouse click - add positive point"""
        x, y = self._canvas_to_image_coords(event.x, event.y)
        if x is not None and y is not None:
            self.viewmodel.add_point_command.execute(x, y, 1)  # Positive point
    
    def _on_right_click(self, event):
        """Handle right mouse click - add negative point"""
        x, y = self._canvas_to_image_coords(event.x, event.y)
        if x is not None and y is not None:
            self.viewmodel.add_point_command.execute(x, y, 0)  # Negative point
    
    def _canvas_to_image_coords(self, canvas_x: int, canvas_y: int):
        """Convert canvas coordinates to image coordinates"""
        if not self.current_image or not self.viewmodel.video_info:
            return None, None
        
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        # Get current image size on canvas
        img_width, img_height = self.current_image.size
        
        # Calculate image position on canvas (centered)
        img_x = (canvas_width - img_width) // 2
        img_y = (canvas_height - img_height) // 2
        
        # Check if click is within image bounds
        if (canvas_x < img_x or canvas_x >= img_x + img_width or
            canvas_y < img_y or canvas_y >= img_y + img_height):
            return None, None
        
        # Convert to image coordinates
        rel_x = canvas_x - img_x
        rel_y = canvas_y - img_y
        
        # Scale to original image size
        original_width = self.viewmodel.video_info.width
        original_height = self.viewmodel.video_info.height
        
        scale_x = original_width / img_width
        scale_y = original_height / img_height
        
        image_x = int(rel_x * scale_x)
        image_y = int(rel_y * scale_y)
        
        return image_x, image_y
    
    def _on_frame_changed(self, property_name: str, old_value, new_value):
        """Handle frame change from viewmodel"""
        frame = self.viewmodel.get_current_frame_with_overlay()
        self.update_frame(frame)


class ControlPanel(ttk.Frame):
    """Control panel with playback controls and frame navigation"""
    
    def __init__(self, parent, viewmodel: VideoLabelerViewModel):
        super().__init__(parent)
        self.viewmodel = viewmodel
        
        self._setup_ui()
        self._bind_viewmodel()
    
    def _setup_ui(self):
        """Setup the control panel UI"""
        # Navigation controls
        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(controls_frame, text="◀◀", command=self._jump_to_start).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="◀", command=self._previous_frame).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="▶", command=self._next_frame).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="▶▶", command=self._jump_to_end).pack(side=tk.LEFT, padx=2)
        
        # Frame info
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, padx=5)
        
        self.frame_var = tk.StringVar(value="Frame: 0/0")
        ttk.Label(info_frame, textvariable=self.frame_var).pack(side=tk.LEFT)
        
        self.time_var = tk.StringVar(value="Time: 0.00s")
        ttk.Label(info_frame, textvariable=self.time_var).pack(side=tk.LEFT, padx=(20, 0))
        
        # Frame slider
        slider_frame = ttk.Frame(self)
        slider_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.frame_slider = ttk.Scale(
            slider_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self._on_slider_change
        )
        self.frame_slider.pack(fill=tk.X)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var).pack(pady=5)
    
    def _bind_viewmodel(self):
        """Bind to viewmodel observable properties"""
        self.viewmodel.add_observer("current_frame_index", self._update_frame_info)
        self.viewmodel.add_observer("status_message", self._update_status)
        self.viewmodel.add_observer("video_loaded", self._update_for_new_video)
    
    def _previous_frame(self):
        self.viewmodel.previous_frame_command.execute()
    
    def _next_frame(self):
        self.viewmodel.next_frame_command.execute()
    
    def _jump_to_start(self):
        self.viewmodel.jump_to_frame_command.execute(0)
    
    def _jump_to_end(self):
        if self.viewmodel.total_frames > 0:
            self.viewmodel.jump_to_frame_command.execute(self.viewmodel.total_frames - 1)
    
    def _on_slider_change(self, value):
        """Handle frame slider change"""
        frame_index = int(float(value))
        self.viewmodel.jump_to_frame_command.execute(frame_index)
    
    def _update_frame_info(self, property_name: str, old_value, new_value):
        """Update frame information display"""
        current_frame = self.viewmodel.current_frame_index
        total_frames = self.viewmodel.total_frames
        current_time = self.viewmodel.current_time
        
        self.frame_var.set(f"Frame: {current_frame + 1}/{total_frames}")
        self.time_var.set(f"Time: {current_time:.2f}s")
        
        # Update slider without triggering callback
        if total_frames > 0:
            self.frame_slider.configure(to=total_frames - 1)
            self.frame_slider.set(current_frame)
    
    def _update_status(self, property_name: str, old_value, new_value):
        """Update status message"""
        self.status_var.set(new_value)
    
    def _update_for_new_video(self, property_name: str, old_value, new_value):
        """Update UI when new video is loaded"""
        self._update_frame_info("current_frame_index", 0, self.viewmodel.current_frame_index)


class MenuBar(tk.Menu):
    """Application menu bar"""
    
    def __init__(self, parent, viewmodel: VideoLabelerViewModel):
        super().__init__(parent)
        self.viewmodel = viewmodel
        
        self._setup_menus()
    
    def _setup_menus(self):
        """Setup menu structure"""
        # File menu
        file_menu = tk.Menu(self, tearoff=0)
        file_menu.add_command(label="Open Video...", command=self._open_video)
        file_menu.add_separator()
        file_menu.add_command(label="Save Annotations...", command=self._save_annotations)
        file_menu.add_command(label="Export COCO...", command=self._export_coco)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._exit_app)
        
        self.add_cascade(label="File", menu=file_menu)
        
        # Help menu
        help_menu = tk.Menu(self, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        
        self.add_cascade(label="Help", menu=help_menu)
    
    def _open_video(self):
        """Open video file dialog"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.viewmodel.load_video_command.execute(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load video:\n{str(e)}")
    
    def _save_annotations(self):
        """Save annotations dialog"""
        if not self.viewmodel.has_annotations:
            messagebox.showwarning("Warning", "No annotations to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Annotations",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.viewmodel.save_annotations_command.execute(file_path)
                messagebox.showinfo("Success", "Annotations saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save annotations:\n{str(e)}")
    
    def _export_coco(self):
        """Export COCO format dialog"""
        if not self.viewmodel.has_annotations:
            messagebox.showwarning("Warning", "No annotations to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export COCO Annotations",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.viewmodel.export_coco_command.execute(file_path)
                messagebox.showinfo("Success", "COCO annotations exported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export COCO:\n{str(e)}")
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "Video Labeling Tool\n\n"
            "MVVM Architecture Demo\n"
            "Uses SAM2 for object segmentation\n\n"
            "Controls:\n"
            "• Left click: Add positive point\n"
            "• Right click: Add negative point\n"
            "• Left/Right arrows: Navigate frames\n"
            "• Space: Next frame\n"
            "• Use File menu to open/save"
        )
    
    def _exit_app(self):
        """Exit application"""
        self.winfo_toplevel().quit()


class VideoLabelerApp(tk.Tk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Video Labeler - MVVM Demo")
        self.geometry("1200x800")
        
        # Initialize ViewModel
        self.viewmodel = VideoLabelerViewModel()
        
        self._setup_ui()
        self._setup_bindings()
    
    def _setup_ui(self):
        """Setup the main UI layout"""
        # Menu bar
        menubar = MenuBar(self, self.viewmodel)
        self.config(menu=menubar)
        
        # Main layout
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video canvas
        self.video_canvas = VideoCanvas(
            main_frame,
            self.viewmodel,
            width=800,
            height=600
        )
        self.video_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Control panel
        self.control_panel = ControlPanel(main_frame, self.viewmodel)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _setup_bindings(self):
        """Setup keyboard shortcuts"""
        # Arrow keys for frame navigation
        self.bind("<Left>", lambda e: self.viewmodel.previous_frame_command.execute())
        self.bind("<Right>", lambda e: self.viewmodel.next_frame_command.execute())
        self.bind("<space>", lambda e: self.viewmodel.next_frame_command.execute())
        
        # Make sure the window can receive focus for key events
        self.focus_set()
    
    def run(self):
        """Start the application"""
        try:
            self.mainloop()
        finally:
            self.viewmodel.cleanup()


if __name__ == "__main__":
    app = VideoLabelerApp()
    app.run()
