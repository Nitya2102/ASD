#!/usr/bin/env python3
"""
Generate test images for manual frontend testing
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create test images directory
test_dir = "test_images"
os.makedirs(test_dir, exist_ok=True)

def create_test_image(filename, color, text):
    """Create a simple test image"""
    img = Image.new('RGB', (224, 224), color=color)
    draw = ImageDraw.Draw(img)
    
    # Add text
    try:
        # Try to use a default font
        draw.text((50, 100), text, fill=(255, 255, 255))
    except:
        # Fallback if font fails
        draw.text((50, 100), text, fill=(255, 255, 255))
    
    filepath = os.path.join(test_dir, filename)
    img.save(filepath)
    print(f"✓ Created: {filepath}")
    return filepath

# Create various test images
print("Creating test images...\n")

create_test_image("test_red.jpg", (200, 0, 0), "Red Image")
create_test_image("test_green.jpg", (0, 200, 0), "Green Image")
create_test_image("test_blue.jpg", (0, 0, 200), "Blue Image")
create_test_image("test_yellow.jpg", (200, 200, 0), "Yellow Image")
create_test_image("test_purple.jpg", (200, 0, 200), "Purple Image")

print(f"\n✓ Test images created in: {os.path.abspath(test_dir)}")
print("\nTo use these images:")
print("1. Open http://localhost:8081")
print("2. Fill out patient info and questionnaire")
print("3. On Image Analysis step, click 'Upload Image'")
print(f"4. Select any file from: {os.path.abspath(test_dir)}")
