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
        Generate GradCAM heatmap using gradient-based visualization
        
        Args:
            img_array: Preprocessed image array (1, 224, 224, 3)
            pred_index: Class index to visualize (None for binary classification)
        
        Returns:
            heatmap: numpy array of shape (224, 224)
        """
        if self.model is None:
            return np.ones((224, 224)) * 0.5
        
        try:
            # For Sequential models with MobileNetV2 base, use input gradients
            img_var = tf.Variable(img_array, dtype=tf.float32)
            
            with tf.GradientTape() as tape:
                tape.watch(img_var)
                predictions = self.model(img_var)
                # Get the prediction (binary classification: 0 or 1)
                pred_class = predictions[0, 0]
            
            # Get gradients with respect to input
            grads = tape.gradient(pred_class, img_var)
            
            if grads is None:
                return np.ones((224, 224)) * 0.5
            
            # Create heatmap from input gradients
            # Take absolute value and average across color channels
            grads_np = grads.numpy()[0]
            heatmap = np.mean(np.abs(grads_np), axis=-1)
            
            # Apply Gaussian blur for smoothing
            heatmap = cv2.GaussianBlur(heatmap, (5, 5), 0)
            
            # Normalize to 0-1
            heatmap_min = np.min(heatmap)
            heatmap_max = np.max(heatmap)
            if heatmap_max > heatmap_min:
                heatmap = (heatmap - heatmap_min) / (heatmap_max - heatmap_min)
            else:
                heatmap = np.ones((224, 224)) * 0.5
            
            return heatmap
            
        except Exception as e:
            print(f"⚠ GradCAM generation failed: {e}")
            return np.ones((224, 224)) * 0.5
    
    def create_heatmap_overlay(self, original_img, heatmap):
        """
        Create visualization overlay of heatmap on original image
        
        Args:
            original_img: PIL Image
            heatmap: numpy array (224, 224)
        
        Returns:
            base64 encoded PNG image
        """
        try:
            # Resize original image
            img_resized = original_img.resize((224, 224))
            img_array = np.array(img_resized).astype(np.float32) / 255.0
            
            # Ensure heatmap is normalized 0-1
            heatmap_normalized = np.clip(heatmap, 0, 1)
            
            # Convert heatmap to uint8 for colormap application
            heatmap_uint8 = np.uint8(255 * heatmap_normalized)
            
            # Apply JET colormap
            heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
            
            # Convert BGR to RGB
            heatmap_rgb = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            
            # Blend: heatmap 40%, original image 60%
            alpha = 0.4
            overlay = heatmap_rgb * alpha + img_array * (1 - alpha)
            overlay = np.clip(overlay, 0, 1)
            
            # Convert to PIL and then to base64
            overlay_img = Image.fromarray(np.uint8(overlay * 255))
            buffer = io.BytesIO()
            overlay_img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return img_base64
        except Exception as e:
            print(f"[ERROR] Heatmap overlay creation failed: {e}")
            return ""
    
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
                    r[0] for r in attention_regions
                ],
                'llm_explanation': text_explanation,
                'facial_regions': [
                    {'region': r[0], 'attention_score': float(r[1]), 'clinical_relevance': ''}
                    for r in attention_regions
                ]
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