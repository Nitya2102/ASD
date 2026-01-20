"""
ASD Explainable AI Module - Lightweight Version
Uses GradCAM and LIME without large model downloads
"""

import tensorflow as tf
import numpy as np
from PIL import Image
import cv2
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Optional LIME import
try:
    from lime import lime_image
    from skimage.segmentation import mark_boundaries
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False
    print("⚠ LIME not installed. Install with: pip install lime scikit-image")


class ASDExplainableAI:
    """Lightweight Explainable AI using GradCAM and LIME"""
    
    def __init__(self, model=None):
        """
        Args:
            model: TensorFlow/Keras model (will be set from unified_asd_api.py)
        """
        print("Initializing Lightweight XAI module...")
        self.model = model
        self.initialized = True
        print(f"✓ XAI module ready (LIME available: {LIME_AVAILABLE})")
    
    def set_model(self, model):
        """Set the CNN model to use for explanations"""
        self.model = model
    
    def generate_gradcam(self, img_array, pred_index=None):
        """
        Generate GradCAM heatmap using TensorFlow/Keras
        
        Args:
            img_array: Preprocessed image array (1, 224, 224, 3)
            pred_index: Class index to visualize (None for binary classification)
        
        Returns:
            heatmap: numpy array of shape (224, 224)
        """
        if self.model is None:
            return np.zeros((224, 224))
        
        # Find the last convolutional layer
        last_conv_layer = None
        for layer in reversed(self.model.layers):
            if len(layer.output_shape) == 4:  # Conv layer has 4D output
                last_conv_layer = layer
                break
        
        if last_conv_layer is None:
            print("⚠ No convolutional layer found for GradCAM")
            return np.zeros((224, 224))
        
        # Create a model that outputs both the conv layer and final prediction
        grad_model = tf.keras.models.Model(
            inputs=[self.model.inputs],
            outputs=[last_conv_layer.output, self.model.output]
        )
        
        # Compute gradient
        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(img_array)
            if pred_index is None:
                pred_index = tf.argmax(predictions[0])
            class_channel = predictions[:, pred_index]
        
        # Gradient of the predicted class with respect to conv layer
        grads = tape.gradient(class_channel, conv_outputs)
        
        # Global average pooling of gradients
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        
        # Weight the channels by importance
        conv_outputs = conv_outputs[0]
        pooled_grads = pooled_grads.numpy()
        conv_outputs = conv_outputs.numpy()
        
        for i in range(pooled_grads.shape[-1]):
            conv_outputs[:, :, i] *= pooled_grads[i]
        
        # Create heatmap
        heatmap = np.mean(conv_outputs, axis=-1)
        heatmap = np.maximum(heatmap, 0)  # ReLU
        heatmap /= (np.max(heatmap) + 1e-10)  # Normalize
        
        # Resize to match input image
        heatmap = cv2.resize(heatmap, (224, 224))
        
        return heatmap
    
    def create_heatmap_overlay(self, original_img, heatmap):
        """
        Create visualization overlay of heatmap on original image
        
        Args:
            original_img: PIL Image
            heatmap: numpy array (224, 224)
        
        Returns:
            base64 encoded PNG image
        """
        # Resize original image
        img_resized = original_img.resize((224, 224))
        img_array = np.array(img_resized) / 255.0
        
        # Apply colormap to heatmap
        heatmap_colored = cv2.applyColorMap(
            np.uint8(255 * heatmap), 
            cv2.COLORMAP_JET
        )
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB) / 255.0
        
        # Superimpose heatmap on image
        overlay = heatmap_colored * 0.4 + img_array * 0.6
        overlay = np.clip(overlay, 0, 1)
        
        # Convert to PIL and then to base64
        overlay_img = Image.fromarray(np.uint8(overlay * 255))
        buffer = io.BytesIO()
        overlay_img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return img_base64
    
    def analyze_attention_regions(self, heatmap):
        """
        Analyze which facial regions receive the most attention
        
        Args:
            heatmap: numpy array (224, 224)
        
        Returns:
            List of (region_name, attention_score) tuples
        """
        h, w = heatmap.shape
        
        # Define approximate facial regions (assuming centered face)
        regions = {
            "upper_face": heatmap[int(0.2*h):int(0.4*h), int(0.2*w):int(0.8*w)].mean(),
            "eyes_region": heatmap[int(0.3*h):int(0.45*h), int(0.25*w):int(0.75*w)].mean(),
            "mid_face": heatmap[int(0.4*h):int(0.6*h), int(0.3*w):int(0.7*w)].mean(),
            "lower_face": heatmap[int(0.6*h):int(0.8*h), int(0.25*w):int(0.75*w)].mean(),
            "overall": heatmap.mean()
        }
        
        # Sort by attention score
        sorted_regions = sorted(regions.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_regions
    
    def generate_lime_explanation(self, img, num_samples=100):
        """
        Generate LIME explanation (optional - only if LIME is installed)
        
        Args:
            img: PIL Image
            num_samples: Number of samples for LIME
        
        Returns:
            base64 encoded image or empty string
        """
        if not LIME_AVAILABLE or self.model is None:
            return ""
        
        try:
            # Prepare image
            img_resized = img.resize((224, 224))
            img_array = np.array(img_resized) / 255.0
            
            # Create LIME explainer
            explainer = lime_image.LimeImageExplainer()
            
            # Prediction function for LIME
            def predict_fn(images):
                preprocessed = images  # Already normalized
                preds = self.model.predict(preprocessed, verbose=0)
                # Return probabilities for both classes
                return np.hstack([1 - preds, preds])
            
            # Generate explanation
            explanation = explainer.explain_instance(
                img_array,
                predict_fn,
                top_labels=1,
                hide_color=0,
                num_samples=num_samples
            )
            
            # Get image with boundaries
            temp, mask = explanation.get_image_and_mask(
                explanation.top_labels[0],
                positive_only=True,
                num_features=5,
                hide_rest=False
            )
            
            # Create visualization
            img_boundry = mark_boundaries(temp, mask)
            
            # Convert to base64
            lime_img = Image.fromarray(np.uint8(img_boundry * 255))
            buffer = io.BytesIO()
            lime_img.save(buffer, format='PNG')
            lime_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return lime_base64
            
        except Exception as e:
            print(f"LIME explanation failed: {e}")
            return ""
    
    def generate_simple_explanation(self, attention_regions):
        """
        Generate simple text explanation based on attention regions
        
        Args:
            attention_regions: List of (region, score) tuples
        
        Returns:
            String explanation
        """
        primary = attention_regions[0]
        secondary = attention_regions[1]
        
        explanation = f"""
**Model Attention Analysis:**

The neural network focused primarily on the **{primary[0]}** (attention: {primary[1]:.2%}), 
followed by the **{secondary[0]}** (attention: {secondary[1]:.2%}).

**Important Note:**
This is a screening tool, not a diagnostic instrument. The model analyzes facial patterns 
that have been studied in autism research literature. However:

- Facial features alone are insufficient for diagnosis
- Many factors influence facial expressions and features
- Professional clinical evaluation is always required
- This tool should only be used as part of comprehensive screening

**Recommendation:**
If screening indicates elevated risk, please consult with a qualified healthcare professional 
for proper evaluation.
        """.strip()
        
        return explanation
    
    def generate_explanation(self, img):
        """
        Complete XAI pipeline - Main method called by unified_asd_api.py
        
        Args:
            img: PIL Image
        
        Returns:
            Dictionary with all explanations
        """
        try:
            # Preprocess image
            img_resized = img.resize((224, 224))
            img_array = np.array(img_resized) / 255.0
            img_batch = np.expand_dims(img_array, axis=0)
            
            # Generate GradCAM heatmap
            heatmap = self.generate_gradcam(img_batch)
            
            # Create heatmap overlay
            heatmap_base64 = self.create_heatmap_overlay(img, heatmap)
            
            # Analyze attention regions
            attention_regions = self.analyze_attention_regions(heatmap)
            
            # Generate LIME (if available)
            lime_base64 = self.generate_lime_explanation(img)
            
            # Generate text explanation
            text_explanation = self.generate_simple_explanation(attention_regions)
            
            return {
                'heatmap_base64': heatmap_base64,
                'lime_base64': lime_base64,
                'attention_regions': [
                    {'region': r[0], 'attention_score': float(r[1])}
                    for r in attention_regions
                ],
                'llm_explanation': text_explanation,
                'facial_regions': {
                    'primary': attention_regions[0][0],
                    'secondary': attention_regions[1][0],
                    'minimal': attention_regions[-1][0]
                }
            }
            
        except Exception as e:
            print(f"Error in XAI pipeline: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'heatmap_base64': '',
                'lime_base64': '',
                'attention_regions': [],
                'llm_explanation': f'Error generating explanation: {str(e)}',
                'facial_regions': {}
            }