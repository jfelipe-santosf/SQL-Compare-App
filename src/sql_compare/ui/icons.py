import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

def create_circle_icon(color: str, size: int = 16) -> ImageTk.PhotoImage:
    """Create a circular icon with the specified color."""
    # Create a transparent background
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a filled circle
    margin = 2
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=color
    )
    
    return ImageTk.PhotoImage(image)

class Icons:
    def __init__(self):
        # Status icons
        self.different = create_circle_icon("#FFA500")  # Orange
        self.source_only = create_circle_icon("#4CAF50")  # Green
        self.target_only = create_circle_icon("#F44336")  # Red
        self.identical = create_circle_icon("#9E9E9E")  # Gray

        # Action icons - could be replaced with actual button icons later
        self.compare = create_circle_icon("#2196F3")  # Blue
        self.update = create_circle_icon("#4CAF50")  # Green
        self.filter = create_circle_icon("#9C27B0")  # Purple
