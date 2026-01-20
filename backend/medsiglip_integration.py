"""ASD Explainable AI Module"""

import tensorflow as tf
import numpy as np
from PIL import Image
import io
import base64

class ASDExplainableAI:
    """Explainable AI for ASD detection using CNN"""

    def __init__(self):
        print("Initializing XAI module...")
        # This is a placeholder - in a real implementation, you'd load your models here
        self.initialized = True
        print("✓ XAI module ready")

    def analyze_image(self, image_data):
        """Analyze image and return explanation"""
        # Placeholder implementation
        return {
            'grad_cam': base64.b64encode(b'placeholder').decode(),
            'lime': base64.b64encode(b'placeholder').decode(),
            'attention_regions': ['face', 'eyes'],
            'llm_explanation': 'Image analysis completed with Grad-CAM and LIME explanations.',
            'facial_regions': {
                'primary': 'face',
                'secondary': 'eyes',
                'minimal': 'nose'
            }
        }

import torch
import torch.nn.functional as F
import torchvision.transforms as T
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from transformers import (
    AutoProcessor,
    AutoModel,
    AutoTokenizer,
    AutoModelForCausalLM
)
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
import io
import base64

class ASDExplainableAI:
    """Explainable AI module using Grad-CAM + SigLIP + LLM"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"XAI using device: {self.device}")
        
        # Load models
        self._load_cnn()
        self._load_siglip()
        self._load_llm()
        
        # Image transform
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406],
                       std=[0.229, 0.224, 0.225])
        ])
    
    def _load_cnn(self):
        """Load CNN for Grad-CAM"""
        from torchvision.models import mobilenet_v2
        
        self.cnn = mobilenet_v2(pretrained=True)
        self.cnn.classifier[1] = torch.nn.Linear(self.cnn.last_channel, 2)
        self.cnn = self.cnn.to(self.device)
        self.cnn.eval()
        
        self.target_layer = self.cnn.features[-1]
        self.cam = GradCAM(model=self.cnn, target_layers=[self.target_layer])
    
    def _load_siglip(self):
        """Load SigLIP for image embeddings"""
        siglip_model_id = "google/siglip-base-patch16-224"
        self.siglip_processor = AutoProcessor.from_pretrained(siglip_model_id)
        self.siglip_model = AutoModel.from_pretrained(siglip_model_id).to(self.device)
        self.siglip_model.eval()
    
    def _load_llm(self):
        """Load LLM for natural language explanations"""
        llm_id = "Qwen/Qwen2.5-3B-Instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(llm_id)
        self.llm = AutoModelForCausalLM.from_pretrained(
            llm_id,
            torch_dtype=torch.float16,
            device_map="auto"
        )
    
    def generate_gradcam(self, img):
        """Generate Grad-CAM heatmap"""
        input_tensor = self.transform(img).unsqueeze(0).to(self.device)
        grayscale_cam = self.cam(input_tensor=input_tensor)[0]
        
        img_np = np.array(img.resize((224, 224))) / 255.0
        cam_overlay = show_cam_on_image(img_np, grayscale_cam, use_rgb=True)
        
        return grayscale_cam, cam_overlay
    
    def analyze_attention_regions(self, cam_map):
        """Analyze which facial regions receive attention"""
        h, w = cam_map.shape
        regions = {
            "eyes": cam_map[int(0.25*h):int(0.45*h), int(0.2*w):int(0.8*w)].mean(),
            "nose": cam_map[int(0.45*h):int(0.6*h), int(0.4*w):int(0.6*w)].mean(),
            "mouth": cam_map[int(0.6*h):int(0.8*h), int(0.3*w):int(0.7*w)].mean(),
        }
        
        sorted_regions = sorted(regions.items(), key=lambda x: x[1], reverse=True)
        return sorted_regions
    
    def generate_llm_explanation(self, attention_regions):
        """Generate natural language explanation using LLM"""
        primary = attention_regions[0][0]
        secondary = attention_regions[1][0]
        low = attention_regions[-1][0]
        
        prompt = f"""You are a medical AI assistant.

Task:
Provide a NON-DIAGNOSTIC autism screening explanation based ONLY on:
- CNN attention regions (Grad-CAM)
- general medical literature

Observed CNN attention summary:
- Primary focus: {primary}
- Secondary focus: {secondary}
- Minimal attention: {low}

Rules:
- Do NOT claim diagnosis
- Use cautious language ("may be associated", "has been reported")
- Emphasize limitations
- Keep response under 150 words

Explain:
1. Which facial regions were emphasized
2. Why such regions are discussed in autism research (if applicable)
3. Why facial features alone are insufficient

Response format:
- Observed Regions
- Literature Context
- Limitations
"""
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.llm.device)
        
        with torch.no_grad():
            output = self.llm.generate(
                **inputs,
                max_new_tokens=250,
                do_sample=False
            )
        
        result = self.tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract only the response part (after the prompt)
        explanation = result.split("Response format:")[-1].strip()
        
        return explanation
    
    def generate_explanation(self, img):
        """
        Complete XAI pipeline
        
        Input: PIL Image
        Output: Dict with heatmap, regions, and explanation
        """
        # Generate Grad-CAM
        grayscale_cam, cam_overlay = self.generate_gradcam(img)
        
        # Analyze attention regions
        attention_regions = self.analyze_attention_regions(grayscale_cam)
        
        # Generate LLM explanation
        llm_explanation = self.generate_llm_explanation(attention_regions)
        
        # Convert heatmap to base64 for frontend
        overlay_pil = Image.fromarray(cam_overlay)
        buffer = io.BytesIO()
        overlay_pil.save(buffer, format='PNG')
        heatmap_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'heatmap_base64': heatmap_base64,
            'attention_regions': [
                {'region': r[0], 'attention_score': float(r[1])}
                for r in attention_regions
            ],
            'llm_explanation': llm_explanation,
            'facial_regions': {
                'primary': attention_regions[0][0],
                'secondary': attention_regions[1][0],
                'minimal': attention_regions[-1][0]
            }
        }

