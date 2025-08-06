import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class ImageCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Cropper - Custom Crop Size")
        self.root.geometry("1200x800")
        
        self.target_width = tk.IntVar(value=1024)
        self.target_height = tk.IntVar(value=1024)
        self.images = []
        self.current_image_index = -1
        self.current_image = None
        self.original_image = None
        self.crop_rect = None
        self.rect_id = None

        # Store crop positions per image
        self.image_crop_positions = {}  
        
        # Variables for dragging
        self.dragging = False
        self.rect_drag_start_x = 0
        self.rect_drag_start_y = 0
        
        self.create_widgets()
        self.setup_bindings()
    
    def create_widgets(self):
        # Top frame for buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Open button
        open_btn = tk.Button(button_frame, text="Select Images", command=self.open_images)
        open_btn.pack(side=tk.LEFT, padx=5)
        
        # Save button
        save_btn = tk.Button(button_frame, text="Save Crop", command=self.save_current_crop)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # Navigation buttons
        self.prev_btn = tk.Button(button_frame, text="Previous", command=self.previous_image, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = tk.Button(button_frame, text="Next", command=self.next_image, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Crop size input frame
        size_frame = tk.Frame(button_frame)
        size_frame.pack(side=tk.LEFT, padx=15)
        
        # Width input
        width_label = tk.Label(size_frame, text="Width:")
        width_label.grid(row=0, column=0, padx=2)
        width_entry = tk.Entry(size_frame, textvariable=self.target_width, width=5)
        width_entry.grid(row=0, column=1, padx=2)
        
        # Height input
        height_label = tk.Label(size_frame, text="Height:")
        height_label.grid(row=0, column=2, padx=2)
        height_entry = tk.Entry(size_frame, textvariable=self.target_height, width=5)
        height_entry.grid(row=0, column=3, padx=2)
        
        # Apply button
        apply_btn = tk.Button(size_frame, text="Apply Size", command=self.apply_crop_size)
        apply_btn.grid(row=0, column=4, padx=5)
        
        # Status label
        self.status_label = tk.Label(button_frame, text="No images loaded")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Canvas for image display
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Instructions label
        instructions = "Enter desired crop dimensions and click 'Apply Size'. Click and drag to move the crop area."
        self.instruction_label = tk.Label(self.root, text=instructions)
        self.instruction_label.pack(side=tk.BOTTOM, pady=10)
    
    def setup_bindings(self):
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
    
    def apply_crop_size(self):
        # Validate inputs
        try:
            width = self.target_width.get()
            height = self.target_height.get()
            
            if width <= 0 or height <= 0:
                raise ValueError("Width and height must be positive")
                
            # If we have an image loaded, update the crop rectangle
            if self.original_image and self.rect_id:
                self.canvas.delete(self.rect_id)
                self.create_fixed_crop_rect()
                
        except tk.TclError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for width and height")
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
    
    def open_images(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        
        if not file_paths:
            return
            
        self.images = list(file_paths)
        
        if len(self.images) > 0:
            self.current_image_index = 0
            self.load_current_image()
            self.update_navigation_buttons()
    
    def load_current_image(self):
        if 0 <= self.current_image_index < len(self.images):
            try:
                # Save the current crop position before loading the new image
                if self.original_image and self.images and self.current_image_index >= 0:
                    current_image_path = self.images[self.current_image_index]
                    self.image_crop_positions[current_image_path] = self.crop_rect

                self.original_image = Image.open(self.images[self.current_image_index])
                self.display_image()
                self.status_label.config(text=f"Image {self.current_image_index + 1} of {len(self.images)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open image: {str(e)}")
    
    def display_image(self):
        if self.original_image:
            # Calculate the scaling to fit in the canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not yet realized, wait a bit
                self.root.after(100, self.display_image)
                return
            
            img_width, img_height = self.original_image.size
            
            # Determine scale factor
            scale_w = canvas_width / img_width
            scale_h = canvas_height / img_height
            scale = min(scale_w, scale_h)
            
            # Resize image for display
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            self.display_scale = scale
            
            resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
            self.current_image = ImageTk.PhotoImage(resized_image)
            
            # Clear previous image and rectangle
            self.canvas.delete("all")
            
            # Calculate centered position
            x_offset = (canvas_width - new_width) // 2
            y_offset = (canvas_height - new_height) // 2
            
            self.image_pos = (x_offset, y_offset)
            self.image_size = (new_width, new_height)
            
            # Draw the image
            self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.current_image)
            
            # Create initial crop rectangle
            self.create_fixed_crop_rect()
    
    def create_fixed_crop_rect(self):
        if not hasattr(self, 'display_scale') or not self.original_image:
            return
            
        # Get current target size
        target_width = self.target_width.get()
        target_height = self.target_height.get()
        
        # Calculate the size of the crop rectangle in display coordinates
        crop_width_display = int(target_width * self.display_scale)
        crop_height_display = int(target_height * self.display_scale)
        
        # Calculate initial position (centered)
        x_offset = max(0, (self.image_size[0] - crop_width_display) // 2)
        y_offset = max(0, (self.image_size[1] - crop_height_display) // 2)
        
        x1 = self.image_pos[0] + x_offset
        y1 = self.image_pos[1] + y_offset
        x2 = x1 + crop_width_display
        y2 = y1 + crop_height_display
        
        # Ensure the rectangle is fully within the image bounds
        x1, y1, x2, y2 = self.constrain_rect_to_image(x1, y1, x2, y2)
        
        # Draw the rectangle
        self.rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2, 
            outline="red", 
            width=2,
            dash=(5, 5)
        )
        self.crop_rect = (x1, y1, x2, y2)
    
    def constrain_rect_to_image(self, x1, y1, x2, y2):
        # Ensure the rectangle stays within image bounds
        rect_width = x2 - x1
        rect_height = y2 - y1
        
        # If the crop size is larger than the image, scale it down
        if rect_width > self.image_size[0]:
            scale = self.image_size[0] / rect_width
            rect_width = self.image_size[0]
            rect_height = int(rect_height * scale)
            
        if rect_height > self.image_size[1]:
            scale = self.image_size[1] / rect_height
            rect_height = self.image_size[1]
            rect_width = int(rect_width * scale)
        
        # Constrain horizontally
        if x1 < self.image_pos[0]:
            x1 = self.image_pos[0]
            x2 = x1 + rect_width
        elif x2 > self.image_pos[0] + self.image_size[0]:
            x2 = self.image_pos[0] + self.image_size[0]
            x1 = x2 - rect_width
        
        # Constrain vertically
        if y1 < self.image_pos[1]:
            y1 = self.image_pos[1]
            y2 = y1 + rect_height
        elif y2 > self.image_pos[1] + self.image_size[1]:
            y2 = self.image_pos[1] + self.image_size[1]
            y1 = y2 - rect_height
        
        return x1, y1, x2, y2
    
    def on_mouse_down(self, event):
        if not self.rect_id:
            return
            
        # Check if the click is inside the rectangle
        x1, y1, x2, y2 = self.crop_rect
        if x1 <= event.x <= x2 and y1 <= event.y <= y2:
            self.dragging = True
            # Store the offset between mouse and rectangle corner
            self.rect_drag_start_x = event.x - x1
            self.rect_drag_start_y = event.y - y1
    
    def on_mouse_drag(self, event):
        if not self.dragging or not self.rect_id:
            return
            
        # Calculate new position
        x1, y1, x2, y2 = self.crop_rect
        rect_width = x2 - x1
        rect_height = y2 - y1
        
        new_x1 = event.x - self.rect_drag_start_x
        new_y1 = event.y - self.rect_drag_start_y
        new_x2 = new_x1 + rect_width
        new_y2 = new_y1 + rect_height
        
        # Constrain to image bounds
        new_x1, new_y1, new_x2, new_y2 = self.constrain_rect_to_image(new_x1, new_y1, new_x2, new_y2)
        
        # Update crop rectangle
        self.canvas.coords(self.rect_id, new_x1, new_y1, new_x2, new_y2)
        self.crop_rect = (new_x1, new_y1, new_x2, new_y2)
    
    def on_mouse_up(self, event):
        self.dragging = False
    
    def save_current_crop(self):
        if not self.crop_rect or not self.original_image:
            messagebox.showwarning("Warning", "No crop area selected!")
            return
            
        # Convert canvas coordinates to original image coordinates
        x1, y1, x2, y2 = self.crop_rect
        x1 = max(0, x1 - self.image_pos[0])
        y1 = max(0, y1 - self.image_pos[1])
        x2 = min(self.image_size[0], x2 - self.image_pos[0])
        y2 = min(self.image_size[1], y2 - self.image_pos[1])
        
        # Scale back to original image size
        img_width, img_height = self.original_image.size
        scale = 1.0 / self.display_scale
        
        x1_orig = int(x1 * scale)
        y1_orig = int(y1 * scale)
        x2_orig = int(x2 * scale)
        y2_orig = int(y2 * scale)
        
        try:
            # Crop the image
            cropped = self.original_image.crop((x1_orig, y1_orig, x2_orig, y2_orig))
            
            # Resize to target size
            target_width = self.target_width.get()
            target_height = self.target_height.get()
            cropped = cropped.resize((target_width, target_height), Image.LANCZOS)
            
            # Get save location
            original_filename = os.path.basename(self.images[self.current_image_index])
            name, ext = os.path.splitext(original_filename)
            
            save_path = filedialog.asksaveasfilename(
                title="Save Cropped Image",
                initialfile=f"{name}_cropped{ext}",
                defaultextension=ext,
                filetypes=[("Image files", f"*{ext}")]
            )
            
            if not save_path:
                return
                
            cropped.save(save_path)
            messagebox.showinfo("Success", f"Image saved to {save_path}")
            
            # Move to next image if available
            if self.current_image_index < len(self.images) - 1:
                self.next_image()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving cropped image: {str(e)}")
    
    def previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_current_image()
            self.update_navigation_buttons()
    
    def next_image(self):
        if self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self.load_current_image()
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        self.prev_btn.config(state=tk.NORMAL if self.current_image_index > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_image_index < len(self.images) - 1 else tk.DISABLED)


def main():
    root = tk.Tk()
    app = ImageCropperApp(root)
    
    # Update the display when window is resized
    def on_resize(event):
        if hasattr(app, 'original_image') and app.original_image:
            app.display_image()
    
    root.bind("<Configure>", on_resize)
    root.mainloop()


if __name__ == "__main__":
    main()
