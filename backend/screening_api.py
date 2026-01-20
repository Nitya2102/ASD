"""
screening_api.py
Questionnaire-based ASD screening API (Frontend-ready)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
from typing import Dict, List

# ============================================================================
# FLASK APP
# ============================================================================

app = Flask(__name__)
CORS(app)

# ============================================================================
# SCREENING ENGINE
# ============================================================================

class ASDScreeningEngine:
    """Questionnaire-based ASD screening engine"""

    def __init__(self, model_path: str = "asd_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.feature_columns = None
        self.model_metadata = None
        self._load_model()

    def _load_model(self):
        with open(self.model_path, "rb") as f:
            data = pickle.load(f)

        self.model = data["model"]
        self.feature_columns = data["feature_columns"]
        self.model_metadata = {
            "training_date": data["training_date"],
            "model_version": data["model_version"],
            "model_type": type(self.model).__name__
        }

        print("✓ Questionnaire ML model loaded")

    # ------------------------------------------------------------------------
    # QUESTIONS
    # ------------------------------------------------------------------------

    def get_questions(self) -> List[Dict]:
        return [
            {"id": "A1", "type": "reverse", "text": "Looks when name is called"},
            {"id": "A2", "type": "reverse", "text": "Makes eye contact easily"},
            {"id": "A3", "type": "reverse", "text": "Points to request objects"},
            {"id": "A4", "type": "reverse", "text": "Points to share interest"},
            {"id": "A5", "type": "reverse", "text": "Engages in pretend play"},
            {"id": "A6", "type": "reverse", "text": "Follows gaze"},
            {"id": "A7", "type": "reverse", "text": "Seeks comfort when upset"},
            {"id": "A8", "type": "reverse", "text": "Typical first words"},
            {"id": "A9", "type": "reverse", "text": "Uses gestures"},
            {"id": "A10", "type": "direct", "text": "Stares at nothing"}
        ]

    # ------------------------------------------------------------------------
    # SCORING
    # ------------------------------------------------------------------------

    def score_responses(self, responses: Dict[str, str]) -> Dict[str, int]:
        scores = {}

        for q in self.get_questions():
            answer = str(responses.get(q["id"], "")).lower()
            yes = answer in ["yes", "y", "1", "true"]

            if q["type"] == "reverse":
                scores[q["id"]] = 0 if yes else 1
            else:
                scores[q["id"]] = 1 if yes else 0

        return scores

    # ------------------------------------------------------------------------
    # INPUT PREP
    # ------------------------------------------------------------------------

    def prepare_input(self, child_info: Dict, scored: Dict[str, int]) -> pd.DataFrame:
        data = {
            "Age": child_info.get("age", 36),
            "Sex": 0 if str(child_info.get("sex", "")).lower() in ["m", "male"] else 1,
            "Jaundice": 1 if str(child_info.get("jaundice", "")).lower() in ["yes", "y", "1", "true"] else 0,
            "Family_mem_with_ASD": 1 if str(child_info.get("family_asd", "")).lower() in ["yes", "y", "1", "true"] else 0,
            **scored
        }

        return pd.DataFrame([{col: data.get(col, 0) for col in self.feature_columns}])

    # ------------------------------------------------------------------------
    # PREDICTION
    # ------------------------------------------------------------------------

    def predict(self, child_info: Dict, responses: Dict[str, str]) -> Dict:
        scored = self.score_responses(responses)
        X = self.prepare_input(child_info, scored)

        pred = int(self.model.predict(X)[0])
        proba = float(self.model.predict_proba(X)[0][1])
        total_score = sum(scored.values())

        if pred == 1:
            risk = "HIGH" if total_score >= 7 else "MODERATE"
        else:
            risk = "LOW"

        return {
            "source": "questionnaire",
            "prediction": pred,
            "prediction_label": "ELEVATED_RISK" if pred else "LOW_RISK",
            "confidence": proba,
            "total_score": total_score,
            "max_score": 10,
            "risk_level": risk,
            "scored_responses": scored
        }

    def get_model_info(self) -> Dict:
        return self.model_metadata


# ============================================================================
# INITIALIZE ENGINE
# ============================================================================

screening_engine = ASDScreeningEngine()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route("/api/screening/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "model_loaded": True,
        "model_info": screening_engine.get_model_info()
    })


@app.route("/api/screening/questions", methods=["GET"])
def questions():
    return jsonify(screening_engine.get_questions())


@app.route("/api/screening/predict", methods=["POST"])
def predict():
    try:
        payload = request.json

        result = screening_engine.predict(
            child_info=payload["child_info"],
            responses=payload["responses"]
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=5001)
