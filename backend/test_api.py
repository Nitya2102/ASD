import requests
import json

# Test the API response
url = "http://localhost:5000/api/predict/image"

# Create a test image
from PIL import Image
import numpy as np
import io

# Create a simple test image
img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
img = Image.fromarray(img_array)

# Convert to bytes
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)

# Send request
files = {'image': ('test.png', img_bytes, 'image/png')}
response = requests.post(url, files=files)

print("Response status:", response.status_code)
print("Response JSON keys:", list(response.json().keys()))

data = response.json()
print(f"\nHeatmapBase64 length: {len(data.get('heatmapBase64', ''))}")
print(f"AttentionRegions: {data.get('attentionRegions', [])}")
print(f"LLM Explanation: {data.get('llmExplanation', '')[:100]}")
print(f"LimeBase64 length: {len(data.get('limeBase64', ''))}")

# Check if heatmap starts with valid base64
heatmap = data.get('heatmapBase64', '')
if heatmap:
    print(f"\nHeatmap base64 start: {heatmap[:50]}")
else:
    print("\n[WARNING] heatmapBase64 is empty!")
