from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pickle
import tensorflow as tf
from PIL import Image
import os

# =====================================================================
# OPTIONAL XAI IMPORT
# =====================================================================
try:
    from medsiglip_integration import ASDExplainableAI
    XAI_AVAILABLE = True
except Exception as e:
    XAI_AVAILABLE = False
    print("⚠ XAI module not available:", e)

# =====================================================================
# FLASK APP
# =====================================================================
app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =====================================================================
# UNIFIED SYSTEM
# =====================================================================

class ASDUnifiedSystem:
    """Unified ASD Detection System with ML + CNN + optional XAI"""

    def __init__(self):
        print("Loading ASD Detection System...\n")
        print(f"TensorFlow version: {tf.__version__}")
        print(f"Keras version: {tf.keras.__version__}\n")

        # -------------------------------------------------------------
        # 1. Load Questionnaire ML Model
        # -------------------------------------------------------------
        ml_path = os.path.join(BASE_DIR, "asd_model.pkl")
        try:
            with open(ml_path, "rb") as f:
                ml_data = pickle.load(f)
            self.ml_model = ml_data["model"]
            self.feature_columns = ml_data["feature_columns"]
            print("✓ ML Model loaded")
        except Exception as e:
            print(f"⚠ ML Model loading failed: {e}")
            self.ml_model = None
            self.feature_columns = None

        # -------------------------------------------------------------
        # 2. Load CNN Model (Fixed for Keras 3.0)
        # -------------------------------------------------------------
        cnn_model_dir = os.path.join(BASE_DIR, "best_asd_mobilenetv2")
        print("Loading CNN model from:", cnn_model_dir)

        try:
            # Verify the directory exists
            if os.path.isdir(cnn_model_dir):
                # List all files in the directory for debugging
                print(f"Files in model directory: {os.listdir(cnn_model_dir)}")
                
                # Load without compiling to avoid BatchNormalization issues
                print("Attempting to load model with compile=False...")
                self.cnn_model = tf.keras.models.load_model(
                    cnn_model_dir,
                    compile=False,  # Skip compilation to avoid layer issues
                    safe_mode=False  # Disable safe mode for compatibility
                )
                
                # Manually compile the model
                print("Manually compiling model...")
                self.cnn_model.compile(
                    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                    loss='binary_crossentropy',
                    metrics=['accuracy']
                )
                
                print("✓ CNN Model loaded successfully")
                print(f"  Model input shape: {self.cnn_model.input_shape}")
                print(f"  Model output shape: {self.cnn_model.output_shape}")
                self.cnn_available = True
                
            else:
                print(f"⚠ CNN Model directory not found at: {cnn_model_dir}")
                self.cnn_model = None
                self.cnn_available = False
                
        except Exception as e:
            print(f"⚠ CNN Model loading failed: {e}")
            print("\n📋 Troubleshooting steps:")
            print("  1. The model may have been saved with an incompatible Keras version")
            print("  2. Try re-saving the model with the current Keras version")
            print("  3. Check if the model directory contains all required files")
            import traceback
            traceback.print_exc()
            self.cnn_model = None
            self.cnn_available = False

        # -------------------------------------------------------------
        # 3. Initialize XAI (optional)
        # -------------------------------------------------------------
        self.xai = None
        if XAI_AVAILABLE:
            try:
                print("Initializing XAI Module (this may download large models)...")
                self.xai = ASDExplainableAI()
                print("✓ XAI Module initialized")
            except Exception as e:
                print("⚠ XAI failed to initialize:", e)
                import traceback
                traceback.print_exc()

        print("\n🎯 System Initialization Complete!\n")
        print(f"Status Summary:")
        print(f"  - ML Model: {'✓ Loaded' if self.ml_model else '✗ Not Available'}")
        print(f"  - CNN Model: {'✓ Loaded' if self.cnn_available else '✗ Not Available'}")
        print(f"  - XAI Module: {'✓ Available' if self.xai else '✗ Not Available'}\n")

    # =================================================================
    # QUESTIONNAIRE PREDICTION
    # =================================================================
    def predict_from_questionnaire(self, questionnaire_data):
        if not self.ml_model:
            return {
                "source": "questionnaire",
                "prediction": 0,
                "confidence": 0.0,
                "error": "ML model not available"
            }
            
        try:
            from screening_api import ASDScreeningEngine

            api = ASDScreeningEngine()
            api.model = self.ml_model
            api.feature_columns = self.feature_columns

            child_info = {
                "age": questionnaire_data["age"],
                "sex": questionnaire_data["sex"],
                "jaundice": questionnaire_data["jaundice"],
                "family_asd": questionnaire_data["family_asd"]
            }

            result = api.predict(child_info, questionnaire_data["responses"])
            return result
            
        except Exception as e:
            print(f"Error in questionnaire prediction: {e}")
            import traceback
            traceback.print_exc()
            return {
                "source": "questionnaire",
                "prediction": 0,
                "confidence": 0.0,
                "error": str(e)
            }

    # =================================================================
    # IMAGE PREDICTION
    # =================================================================
    def predict_from_image(self, image_file):
        if not self.cnn_available:
            return {
                "source": "image",
                "prediction": 0,
                "confidence": 0.0,
                "error": "CNN model not available",
                "heatmap_base64": "",
                "attention_regions": [],
                "llm_explanation": "CNN model could not be loaded",
                "facial_regions": {}
            }

        try:
            # Load and preprocess image
            img = Image.open(image_file).convert("RGB")
            img_resized = img.resize((224, 224))
            img_array = np.array(img_resized) / 255.0
            img_batch = np.expand_dims(img_array, axis=0)

            # Get prediction from CNN
            print("Running CNN prediction...")
            cnn_pred = float(self.cnn_model.predict(img_batch, verbose=0)[0][0])
            print(f"CNN prediction: {cnn_pred:.4f}")

            # Get XAI explanation if available
            if self.xai:
                print("Generating XAI explanation...")
                xai_results = self.xai.generate_explanation(img)
            else:
                xai_results = {
                    "heatmap_base64": "",
                    "attention_regions": [],
                    "llm_explanation": "Explainable AI module not available",
                    "facial_regions": {}
                }

            return {
                "source": "image",
                "prediction": int(cnn_pred > 0.5),
                "confidence": cnn_pred,
                **xai_results
            }
            
        except Exception as e:
            print(f"Error during image prediction: {e}")
            import traceback
            traceback.print_exc()
            return {
                "source": "image",
                "prediction": 0,
                "confidence": 0.0,
                "error": str(e),
                "heatmap_base64": "",
                "attention_regions": [],
                "llm_explanation": f"Error during prediction: {str(e)}",
                "facial_regions": {}
            }

    # =================================================================
    # COMBINED PREDICTION
    # =================================================================
    def combined_prediction(self, questionnaire_result, image_result):
        ml_weight = 0.4
        cnn_weight = 0.6

        # Handle cases where one model might have failed
        q_conf = questionnaire_result.get("confidence", 0.0)
        i_conf = image_result.get("confidence", 0.0)

        combined_confidence = (q_conf * ml_weight + i_conf * cnn_weight)

        final_prediction = int(combined_confidence > 0.5)

        if combined_confidence > 0.75:
            risk_level = "HIGH"
        elif combined_confidence > 0.5:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        return {
            "prediction": final_prediction,
            "prediction_label": "ELEVATED_RISK" if final_prediction else "LOW_RISK",
            "confidence": combined_confidence,
            "risk_level": risk_level,
            "questionnaire_details": questionnaire_result,
            "image_details": image_result
        }

# =====================================================================
# INITIALIZE SYSTEM
# =====================================================================
print("="*70)
print("Starting ASD Detection System...")
print("="*70)
asd_system = ASDUnifiedSystem()
print("="*70)

# =====================================================================
# API ENDPOINTS
# =====================================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "models_loaded": {
            "ml_model": asd_system.ml_model is not None,
            "cnn_model": asd_system.cnn_available,
            "xai_module": asd_system.xai is not None
        },
        "tensorflow_version": tf.__version__,
        "keras_version": tf.keras.__version__
    })

@app.route("/api/predict/questionnaire", methods=["POST"])
def predict_questionnaire():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        result = asd_system.predict_from_questionnaire(data)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in questionnaire prediction endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/predict/image", methods=["POST"])
def predict_image():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image provided"}), 400
            
        image_file = request.files["image"]
        if image_file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
            
        result = asd_system.predict_from_image(image_file)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in image prediction endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/predict/combined", methods=["POST"])
def predict_combined():
    try:
        import json

        questionnaire_result = None
        image_result = None

        # Get questionnaire data if provided
        if request.form.get("data"):
            try:
                questionnaire_data = json.loads(request.form["data"])
                questionnaire_result = asd_system.predict_from_questionnaire(questionnaire_data)
            except Exception as e:
                print(f"Error processing questionnaire data: {e}")

        # Get image prediction if provided
        if "image" in request.files:
            try:
                image_result = asd_system.predict_from_image(request.files["image"])
            except Exception as e:
                print(f"Error processing image: {e}")

        # Return combined or individual results
        if questionnaire_result and image_result:
            return jsonify(asd_system.combined_prediction(questionnaire_result, image_result))
        elif questionnaire_result:
            return jsonify(questionnaire_result)
        elif image_result:
            return jsonify(image_result)
        else:
            return jsonify({"error": "No valid data provided"}), 400
            
    except Exception as e:
        print(f"Error in combined prediction endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# =====================================================================
# RUN
# =====================================================================
if __name__ == "__main__":
    print("\n🚀 Starting Flask server on http://localhost:5000")
    print("Press CTRL+C to quit\n")
    app.run(debug=True, port=5000, host='0.0.0.0')