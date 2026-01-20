# Frontend CNN Predictions - Debugging Guide

## Step-by-Step Testing Procedure

### Prerequisites
Make sure both services are running:
```powershell
# Terminal 1 - Backend
cd c:\Users\prart\cpp_projects\ML\ASD\backend
python unified_asd_api.py

# Terminal 2 - Frontend
cd c:\Users\prart\cpp_projects\ML\ASD\frontend
npm run dev
```

### Frontend URL
Open: http://localhost:8081

---

## Test Flow with Console Monitoring

### 1. OPEN BROWSER CONSOLE
- Press **F12** to open Developer Tools
- Go to **Console** tab
- Keep this open throughout the test

### 2. FILL PATIENT INFO
- **Enter Age:** 5
- **Select Sex:** Male
- **Jaundice:** No
- **Family ASD:** No
- **Click Next**

**What to see in console:**
```
[ScreeningWizard] State: {
  step: 'questionnaire',
  hasPatientInfo: true,
  ...
}
```

### 3. ANSWER QUESTIONNAIRE
- Answer all 10 questions (any answers work)
- **Click Submit Questionnaire**

**What to see in console:**
```
[Frontend] Questionnaire API Response: {
  source: 'questionnaire',
  prediction: 0,
  confidence: 0.0004,
  ...
}

[Frontend] Parsed QuestionnaireResult: {...}

[ScreeningWizard] State: {
  step: 'image-analysis',
  hasQuestionnaireResult: true,
  ...
}
```

### 4. UPLOAD/CAPTURE IMAGE
- Upload an image or take a photo
- Image should appear in preview
- **Click Analyze Image**

**What to see in console:**
```
[Frontend] Image API Response: {
  source: 'image',
  prediction: 1,
  confidence: 0.9982,
  attention_regions: [],
  ...
}

[Frontend] Parsed ImageResult: {...}

[Frontend] Combined Result: {
  mlConfidence: 0.0004,
  cnnConfidence: 0.9982,
  combinedConfidence: 0.9302,
  riskLevel: 'HIGH'
}

[Frontend] Final Combined Result: {...}

[ScreeningWizard] State: {
  step: 'results',
  hasCombinedResult: true,
  ...
}
```

### 5. VIEW RESULTS PAGE
After step 4, you should automatically navigate to Results page

**What you should see:**
- Left column: **Questionnaire Analysis**
  - ML Model Confidence
  - Total Score
  - Contribution (40%)
- Right column: **Image Analysis** ← CNN PREDICTIONS
  - CNN Model Confidence ✨
  - Prediction Label
  - Contribution (60%)

---

## Troubleshooting

### Issue: Stuck at Image Analysis Step

**Check in Console:**
```javascript
// Look for this log
[Frontend] Image API Response:
```

If not present:
1. Network error - check Network tab (F12 → Network)
2. Backend not running - check backend terminal for errors
3. Image file too large - try smaller image

### Issue: Results Page Shows "Error: No results available"

**In Console check:**
```javascript
[ScreeningWizard] State: {
  step: 'results',
  hasCombinedResult: false,  // ← Should be TRUE
  ...
}
```

If `hasCombinedResult` is false, check:
1. Did image API return successfully?
2. Is `submitImage` catching an error?
3. Look for `[Frontend] Image submission error:` in console

### Issue: CNN Confidence Shows as 0 or NaN

**Possible causes:**
- `data.confidence` is undefined or null
- Type casting issue
- Backend returning unexpected format

**Check in console:**
```javascript
[Frontend] Image API Response: {
  confidence: 0.9982  // Should be a number
}
```

### Issue: Results Show But CNN Values Are Missing

**Check:**
1. Is the image prediction showing at all?
2. Are there JavaScript errors in console?
3. Does `result.imageDetails` have data?

---

## Console Logs Reference

### Expected Logs During Normal Flow

1. **Patient Info Submitted:**
   ```
   [ScreeningWizard] State: { step: 'questionnaire', hasPatientInfo: true }
   ```

2. **Questionnaire Submitted:**
   ```
   [Frontend] Questionnaire API Response: {...}
   [Frontend] Parsed QuestionnaireResult: {...}
   [ScreeningWizard] State: { step: 'image-analysis', hasQuestionnaireResult: true }
   ```

3. **Image Submitted:**
   ```
   [Frontend] Image API Response: {...}
   [Frontend] Parsed ImageResult: {...}
   [Frontend] Combined Result: {...}
   [Frontend] Final Combined Result: {...}
   [ScreeningWizard] State: { step: 'results', hasCombinedResult: true }
   ```

---

## Network Tab Debugging

**F12 → Network Tab:**

### Check Image Prediction Request
1. Look for `/api/predict/image` request
2. Click on it
3. **Response tab** should show:
   ```json
   {
     "source": "image",
     "prediction": 1,
     "confidence": 0.9982,
     ...
   }
   ```

### Check Questionnaire Request
1. Look for `/api/predict/questionnaire` request
2. **Response tab** should show:
   ```json
   {
     "source": "questionnaire",
     "prediction": 0,
     "confidence": 0.0004,
     ...
   }
   ```

---

## Quick Checklist

- [ ] Browser console is open (F12)
- [ ] Backend terminal shows model is loaded
- [ ] Backend logs show predictions being output
- [ ] Frontend console shows `[Frontend] Image API Response:`
- [ ] Frontend shows results page navigation
- [ ] Results page displays both Questionnaire and Image Analysis
- [ ] CNN confidence value is visible and not zero/NaN
- [ ] Combined risk level is calculated correctly

---

## If Everything Fails

Try this complete reset:

```powershell
# Terminal 1 - Kill and restart backend
Get-Process python | Stop-Process
cd c:\Users\prart\cpp_projects\ML\ASD\backend
python unified_asd_api.py

# Terminal 2 - Kill and restart frontend
Get-Process npm | Stop-Process
cd c:\Users\prart\cpp_projects\ML\ASD\frontend
npm run dev

# Browser - Clear cache
Press Ctrl+Shift+R  # Hard refresh

# Try the flow again
```

---

## Contact Backend for Verification

To verify backend is working independently:
```powershell
cd c:\Users\prart\cpp_projects\ML\ASD
python test_cnn_predictions.py
```

This will test all endpoints directly without frontend.
