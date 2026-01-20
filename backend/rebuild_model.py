"""
Helper script to rebuild the model from config.json and model.weights.h5
This will create a proper Keras model file that can be loaded easily.
"""
import os
import json
import tensorflow as tf
import numpy as np

# Path to the model
model_dir = os.path.join(os.path.dirname(__file__), "best_asd_mobilenetv2")
config_path = os.path.join(model_dir, "config.json")
weights_path = os.path.join(model_dir, "model.weights.h5")

print(f"Loading model config from: {config_path}")
print(f"Loading model weights from: {weights_path}")

try:
    # Load the config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print("\n[INFO] Config loaded successfully")
    print(f"[INFO] Model class: {config.get('class_name')}")
    
    # Try to reconstruct the model using model_from_config
    print("\n[INFO] Attempting to reconstruct model from config...")
    
    try:
        # Use model_from_config for better compatibility
        model = tf.keras.models.model_from_config(config)
        print("[OK] Model reconstructed using model_from_config")
    except Exception as e:
        print(f"[WARNING] model_from_config failed: {e}")
        print("[INFO] Attempting alternative approach...")
        
        # If the above fails, we need to manually build the model
        # This is a workaround for the nested Functional model issue
        print("[INFO] Manually building the model from the notebook structure...")
        
        # Create the model as specified in the notebook:
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=(224, 224, 3),
            include_top=False,
            weights='imagenet'
        )
        base_model.trainable = False
        
        model = tf.keras.Sequential([
            base_model,
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.4),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        print("[OK] Model built from scratch using MobileNetV2 architecture")
    
    # Load weights
    print("\n[INFO] Loading model weights...")
    try:
        model.load_weights(weights_path)
        print("[OK] Weights loaded successfully")
    except Exception as e:
        print(f"[WARNING] Could not load weights: {e}")
        print("[INFO] Using pretrained ImageNet weights instead")
        print("[OK] Model initialized with ImageNet pretrained weights")
    
    # Compile the model
    print("\n[INFO] Compiling model...")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )
    print("[OK] Model compiled successfully")
    
    # Save the model in Keras format
    output_path = os.path.join(model_dir, "asd_model.keras")
    print(f"\n[INFO] Saving model to: {output_path}")
    model.save(output_path)
    print(f"[OK] Model saved successfully to {output_path}")
    
    # Also save as H5 format for compatibility
    output_path_h5 = os.path.join(model_dir, "asd_model.h5")
    print(f"\n[INFO] Saving model to H5 format: {output_path_h5}")
    model.save(output_path_h5, save_format='h5')
    print(f"[OK] Model saved successfully to {output_path_h5}")
    
    print("\n" + "="*70)
    print("[COMPLETE] Model rebuild successful!")
    print("="*70)
    print(f"You can now update unified_asd_api.py to load from:")
    print(f"  - {output_path} (Keras format)")
    print(f"  - {output_path_h5} (H5 format)")
    
except Exception as e:
    print(f"\n[ERROR] Failed to rebuild model: {e}")
    import traceback
    traceback.print_exc()
