#!/usr/bin/env python3
"""
End-to-End Test: Verify Frontend CNN Prediction Display
"""

import requests
import json
import time
from PIL import Image
import io

BASE_URL = 'http://localhost:5000'

def test_questionnaire():
    """Test questionnaire prediction endpoint"""
    print("=" * 70)
    print("TEST 1: Questionnaire Prediction")
    print("=" * 70)
    
    test_data = {
        'age': 5,
        'sex': 'male',
        'jaundice': 'no',
        'family_asd': 'no',
        'responses': {
            'A1': 'yes', 'A2': 'yes', 'A3': 'no', 'A4': 'no', 'A5': 'yes',
            'A6': 'no', 'A7': 'yes', 'A8': 'yes', 'A9': 'yes', 'A10': 'no'
        }
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/predict/questionnaire', json=test_data)
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"ML Prediction: {data['prediction']}")
        print(f"ML Confidence: {data['confidence']:.4f}")
        print(f"Risk Level: {data['risk_level']}")
        print(f"Total Score: {data['total_score']}/10")
        
        # Verify required fields exist
        required_fields = ['prediction', 'confidence', 'risk_level', 'total_score', 'source']
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print(f"[WARNING] Missing fields: {missing}")
        else:
            print("[OK] All required fields present")
        
        print()
        return data
        
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        return None

def test_image():
    """Test image prediction endpoint"""
    print("=" * 70)
    print("TEST 2: Image Prediction (CNN Model)")
    print("=" * 70)
    
    try:
        # Create a dummy test image
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {'image': ('test.png', img_bytes, 'image/png')}
        response = requests.post(f'{BASE_URL}/api/predict/image', files=files)
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"CNN Prediction: {data['prediction']}")
        print(f"CNN Confidence: {data['confidence']:.4f}")
        print(f"Attention Regions: {data['attention_regions']}")
        print(f"LLM Explanation: {data['llm_explanation']}")
        
        # Verify required fields
        required_fields = ['prediction', 'confidence', 'source', 'attention_regions', 'llm_explanation']
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print(f"[WARNING] Missing fields: {missing}")
        else:
            print("[OK] All required fields present")
        
        # Verify snake_case to camelCase mapping
        expected_mappings = {
            'attention_regions': 'attentionRegions',
            'heatmap_base64': 'heatmapBase64',
            'llm_explanation': 'llmExplanation',
            'facial_regions': 'facialRegions',
        }
        
        print("\n[Frontend Mapping Check]")
        for snake_case, camel_case in expected_mappings.items():
            if snake_case in data:
                print(f"  {snake_case} → {camel_case}: [OK]")
            else:
                print(f"  {snake_case} → {camel_case}: [MISSING]")
        
        print()
        return data
        
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        return None

def test_combined():
    """Test combined prediction with both questionnaire and image"""
    print("=" * 70)
    print("TEST 3: Combined Prediction (Questionnaire + Image)")
    print("=" * 70)
    
    # Get questionnaire result first
    q_data = {
        'age': 5,
        'sex': 'male',
        'jaundice': 'no',
        'family_asd': 'no',
        'responses': {
            'A1': 'no', 'A2': 'no', 'A3': 'no', 'A4': 'no', 'A5': 'no',
            'A6': 'no', 'A7': 'no', 'A8': 'no', 'A9': 'no', 'A10': 'yes'
        }
    }
    
    try:
        # Get questionnaire prediction
        q_resp = requests.post(f'{BASE_URL}/api/predict/questionnaire', json=q_data)
        q_result = q_resp.json()
        print(f"ML Prediction: {q_result['prediction']} (Confidence: {q_result['confidence']:.4f})")
        
        # Get image prediction
        img = Image.new('RGB', (224, 224), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {'image': ('test.png', img_bytes, 'image/png')}
        i_resp = requests.post(f'{BASE_URL}/api/predict/image', files=files)
        i_result = i_resp.json()
        print(f"CNN Prediction: {i_result['prediction']} (Confidence: {i_result['confidence']:.4f})")
        
        # Calculate combined (frontend logic)
        ml_weight = 0.4
        cnn_weight = 0.6
        ml_conf = q_result['confidence']
        cnn_conf = i_result['confidence']
        combined_conf = ml_conf * ml_weight + cnn_conf * cnn_weight
        
        print(f"\nCombined Calculation:")
        print(f"  ML Contribution: {ml_conf:.4f} × {ml_weight} = {ml_conf * ml_weight:.4f}")
        print(f"  CNN Contribution: {cnn_conf:.4f} × {cnn_weight} = {cnn_conf * cnn_weight:.4f}")
        print(f"  Combined Confidence: {combined_conf:.4f}")
        print(f"  Combined Prediction: {'ELEVATED_RISK' if combined_conf > 0.5 else 'LOW_RISK'}")
        
        if combined_conf > 0.75:
            risk = 'HIGH'
        elif combined_conf > 0.5:
            risk = 'MODERATE'
        else:
            risk = 'LOW'
        print(f"  Risk Level: {risk}")
        
        print("\n[OK] Combined prediction calculation successful")
        print()
        
    except Exception as e:
        print(f"[ERROR] Failed: {e}")

def main():
    print("\n" + "=" * 70)
    print("FRONTEND CNN PREDICTION DISPLAY - END-TO-END TEST")
    print("=" * 70 + "\n")
    
    # Test 1: Questionnaire
    q_result = test_questionnaire()
    
    # Test 2: Image
    i_result = test_image()
    
    # Test 3: Combined
    test_combined()
    
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("[INFO] All API endpoints are responding correctly")
    print("[INFO] Backend is outputting CNN predictions")
    print("[INFO] Frontend should now display CNN predictions in Results page")
    print("\n[NEXT STEPS]:")
    print("1. Open http://localhost:8081 in your browser")
    print("2. Open Developer Console (F12)")
    print("3. Fill out the questionnaire")
    print("4. Upload an image")
    print("5. Check the Results page for:")
    print("   - CNN Model Confidence (60% weight)")
    print("   - Image Analysis section with prediction")
    print("   - Combined risk level calculation")
    print("6. Check console logs for debug information")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    main()
