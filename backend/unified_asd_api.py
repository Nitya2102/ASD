from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import numpy as np
import pickle
import sys
import tensorflow as tf
from PIL import Image
import os

# =====================================================================
# OPTIONAL FACE DETECTION IMPORT
# =====================================================================
try:
    import cv2
    FACE_DETECTION_AVAILABLE = True
except Exception as e:
    FACE_DETECTION_AVAILABLE = False
    print("[WARNING] Face detection not available:", e)

# =====================================================================
# OPTIONAL XAI IMPORT
# =====================================================================
try:
    from medsiglip_integration import ASDExplainableAI
    XAI_AVAILABLE = True
except Exception as e:
    XAI_AVAILABLE = False
    print("[WARNING] XAI module not available:", e)

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

        # -----
        # 1. Load Questionnaire ML Model (Optional)
        # -----
        ml_path = os.path.join(BASE_DIR, "best_asd_mobilenetv2", "asd_model.pkl")
        try:
            # Workaround for numpy <2 / scikit-learn version mismatch
            import warnings
            warnings.filterwarnings("ignore", category=UserWarning)
            
            if os.path.exists(ml_path):
                with open(ml_path, "rb") as f:
                    ml_data = pickle.load(f)
                self.ml_model = ml_data["model"]
                self.feature_columns = ml_data["feature_columns"]
                print("[OK] ML Model loaded")
            else:
                print("[INFO] ML Model file not found (asd_model.pkl) - Questionnaire-based detection disabled")
                self.ml_model = None
                self.feature_columns = None
        except Exception as e:
            print(f"[INFO] ML Model skipped: {e}")
            self.ml_model = None
            self.feature_columns = None

        # -----
        # 2. Load CNN Model (Keras format)
        # -----
        cnn_model_path = os.path.join(BASE_DIR, "best_asd_mobilenetv2", "asd_model.keras")
        print(f"Loading CNN model from: {cnn_model_path}")

        try:
            if os.path.exists(cnn_model_path):
                print("[INFO] Loading Keras model...")
                self.cnn_model = tf.keras.models.load_model(cnn_model_path)
                
                print("[OK] CNN Model loaded successfully")
                print(f"  Model input shape: {self.cnn_model.input_shape}")
                print(f"  Model output shape: {self.cnn_model.output_shape}")
                self.cnn_available = True
                
            else:
                print(f"[ERROR] Model file not found at: {cnn_model_path}")
                print(f"[INFO] Please run: python rebuild_model.py")
                print(f"[INFO] This will create the asd_model.keras file from config.json + model.weights.h5")
                self.cnn_model = None
                self.cnn_available = False
                
        except Exception as e:
            print(f"[ERROR] CNN Model loading failed: {e}")
            print("[INFO] Troubleshooting:")
            print("  1. Check if best_asd_mobilenetv2/asd_model.keras exists")
            print("  2. Run: python rebuild_model.py")
            print("  3. Check TensorFlow and Keras versions")
            import traceback
            traceback.print_exc()
            self.cnn_model = None
            self.cnn_available = False

        # -----
        # 3. Initialize Face Detection (optional)
        # -----
        self.face_detector = None
        self.face_detection_available = False
        if FACE_DETECTION_AVAILABLE:
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                detector = cv2.CascadeClassifier(cascade_path)
                if detector.empty():
                    raise ValueError("Haar cascade could not be loaded")
                self.face_detector = detector
                self.face_detection_available = True
                print("[OK] Face detection initialized")
            except Exception as e:
                print("[WARNING] Face detection unavailable:", e)

        # -----
        # 4. Initialize XAI (optional)
        # -----
        self.xai = None
        if XAI_AVAILABLE and self.cnn_available:
            try:
                print("Initializing XAI Module...")
                self.xai = ASDExplainableAI(model=self.cnn_model)
                print("[OK] XAI Module initialized")
            except Exception as e:
                print("[WARNING] XAI failed to initialize:", e)
                import traceback
                traceback.print_exc()
        elif XAI_AVAILABLE and not self.cnn_available:
            print("[WARNING] XAI skipped: CNN model not available")

        print("\n[OK] System Initialization Complete!\n")
        print(f"Status Summary:")
        ml_status = '[OK] Loaded' if self.ml_model else '[INFO] Skipped (numpy BitGenerator incompatibility)'
        print(f"  - ML Model: {ml_status}")
        print(f"  - CNN Model: {'[OK] Loaded' if self.cnn_available else '[FAIL] Not Available'}")
        print(f"  - XAI Module: {'[OK] Available' if self.xai else '[FAIL] Not Available'}\n")

    # =================================================================
    # QUESTIONNAIRE PREDICTION
    # =================================================================
    def predict_from_questionnaire(self, questionnaire_data):
        """Predict from questionnaire; if ML model missing, use heuristic fallback."""
        # Heuristic fallback when pickle model is unavailable
        def fallback_predict(data):
            # Scoring rules mirror screening_api.py
            questions = [
                {"id": "A1", "type": "reverse"},
                {"id": "A2", "type": "reverse"},
                {"id": "A3", "type": "reverse"},
                {"id": "A4", "type": "reverse"},
                {"id": "A5", "type": "reverse"},
                {"id": "A6", "type": "reverse"},
                {"id": "A7", "type": "reverse"},
                {"id": "A8", "type": "reverse"},
                {"id": "A9", "type": "reverse"},
                {"id": "A10", "type": "direct"},
            ]

            responses = data.get("responses", {})
            scores = {}
            for q in questions:
                ans = str(responses.get(q["id"], "")).lower()
                yes = ans in ["yes", "y", "1", "true"]
                scores[q["id"]] = 0 if (yes and q["type"] == "reverse") else (1 if (yes and q["type"] == "direct") else (1 if q["type"] == "reverse" else 0))

            total_score = sum(scores.values())
            confidence = total_score / 10.0
            prediction = int(total_score >= 5)
            if total_score >= 8:
                risk = "HIGH"
            elif total_score >= 5:
                risk = "MODERATE"
            else:
                risk = "LOW"

            return {
                "source": "questionnaire",
                "prediction": prediction,
                "prediction_label": "ELEVATED_RISK" if prediction else "LOW_RISK",
                "confidence": confidence,
                "total_score": total_score,
                "max_score": 10,
                "risk_level": risk,
                "scored_responses": scores,
                "fallback": True
            }

        if not self.ml_model:
            return fallback_predict(questionnaire_data)
            
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
            result["fallback"] = False
            return result
            
        except Exception as e:
            print(f"Error in questionnaire prediction: {e}")
            import traceback
            traceback.print_exc()
            return fallback_predict(questionnaire_data)

    # =================================================================
    # IMAGE PREDICTION
    # =================================================================
    def _check_face(self, img: Image.Image):
        if not self.face_detection_available:
            return {
                "has_face": True,
                "face_count": 0,
                "is_dummy": False,
                "reason": "face_detection_unavailable",
                "message": "Face detection unavailable; skipping check."
            }

        img_rgb = np.array(img)
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        print(f"[DEBUG] Image size for face detection: {gray.shape}")
        
        # Try multiple detection approaches with more lenient parameters
        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.05,  # More sensitive
            minNeighbors=3,    # Less strict
            minSize=(30, 30),  # Smaller minimum size
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # If no faces found with strict parameters, try even more lenient
        if len(faces) == 0:
            faces = self.face_detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=2,
                minSize=(20, 20),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
        
        face_count = len(faces)
        print(f"[DEBUG] Detected {face_count} faces: {faces.tolist() if len(faces) > 0 else 'None'}")

        face_count = len(faces)
        print(f"[DEBUG] Detected {face_count} faces: {faces.tolist() if len(faces) > 0 else 'None'}")

        if face_count == 0:
            return {
                "has_face": False,
                "face_count": 0,
                "is_dummy": True,
                "reason": "no_face",
                "message": "No face detected. Please upload a clear frontal face image."
            }

        if face_count > 1:
            # Allow multiple faces but warn about it
            print(f"[DEBUG] Multiple faces detected ({face_count}), proceeding with analysis")
            return {
                "has_face": True,
                "face_count": face_count,
                "is_dummy": False,  # Don't block multiple faces for now
                "reason": "multiple_faces_allowed",
                "message": f"Multiple faces detected ({face_count}), using largest detected face."
            }

        return {
            "has_face": True,
            "face_count": face_count,
            "is_dummy": False,
            "reason": "single_face",
            "message": "Face detected"
        }

    def predict_from_image(self, image_file):
        if not self.cnn_available:
            return {
                "source": "image",
                "prediction": 0,
                "confidence": 0.0,
                "error": "CNN model not available",
                "face_check": {
                    "has_face": False,
                    "face_count": 0,
                    "is_dummy": False,
                    "reason": "cnn_unavailable",
                    "message": "CNN model not available"
                },
                "heatmap_base64": "",
                "attention_regions": [],
                "llm_explanation": "CNN model could not be loaded",
                "facial_regions": {}
            }

        try:
            # Load and preprocess image
            img = Image.open(image_file).convert("RGB")

            # Face check (reject non-face or dummy images)
            face_check = self._check_face(img)
            if face_check.get("is_dummy"):
                return {
                    "source": "image",
                    "prediction": 0,
                    "confidence": 0.0,
                    "error": face_check.get("message", "No valid face detected"),
                    "face_check": face_check,
                    "heatmap_base64": "",
                    "attention_regions": [],
                    "llm_explanation": face_check.get("message", "No valid face detected"),
                    "facial_regions": {}
                }

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
                "face_check": face_check,
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
                "face_check": {
                    "has_face": False,
                    "face_count": 0,
                    "is_dummy": False,
                    "reason": "prediction_error",
                    "message": str(e)
                },
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
# ROOT INDEX
# =====================================================================
@app.route("/", methods=["GET"])
def index():
    """Redirect root to the health endpoint."""
    return redirect("/api/health")

# =====================================================================
# DEBUG: ROUTES INSPECTION
# =====================================================================
@app.route("/api/debug/routes", methods=["GET"])
def debug_routes():
    """Return a JSON list of registered routes and their methods for debugging."""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "rule": str(rule),
            "methods": sorted([m for m in rule.methods if m not in ("HEAD", "OPTIONS")]),
            "endpoint": rule.endpoint
        })
    return jsonify({"routes": routes})

# =====================================================================
# RUN
# =====================================================================
if __name__ == "__main__":
    print("\n[INFO] Starting Flask server on http://localhost:5000")
    print("Press CTRL+C to quit\n")
    app.run(debug=True, port=5000, host='0.0.0.0')
