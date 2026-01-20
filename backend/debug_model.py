import tensorflow as tf
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cnn_model_path = os.path.join(BASE_DIR, "best_asd_mobilenetv2", "asd_model.keras")

print("Loading model...")
model = tf.keras.models.load_model(cnn_model_path)

print(f"\nModel type: {type(model)}")
print(f"Total layers: {len(model.layers)}\n")

print("Layer structure:")
for i, layer in enumerate(model.layers):
    layer_type = layer.__class__.__name__
    output_shape = layer.output_shape
    print(f"  {i}: {layer.name:30s} | {layer_type:20s} | Output: {output_shape}")

print("\n\nSearching for convolutional layers...")
for i, layer in enumerate(model.layers):
    if 'Conv' in layer.__class__.__name__ or 'conv' in layer.name.lower():
        print(f"  Found: Layer {i} - {layer.name} ({layer.__class__.__name__})")
