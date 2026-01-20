# Quick Reference: CNN Predictions in Frontend

## 🎯 What Was Fixed
The frontend now properly displays CNN predictions from the backend in the Results page.

## 📍 Where to See CNN Predictions

**Results Page → Image Analysis Card (Right Column)**
- Shows CNN Model Confidence percentage
- Shows Prediction label (Elevated Risk / Low Risk)
- Shows CNN's contribution to overall risk (60%)

## 🔍 How to Test

### 1. Start Everything
```powershell
# Backend (Terminal 1)
cd c:\Users\prart\cpp_projects\ML\ASD\backend
python unified_asd_api.py

# Frontend (Terminal 2)
cd c:\Users\prart\cpp_projects\ML\ASD\frontend
npm run dev
```

### 2. Open Browser
- Go to: http://localhost:8081
- Open Developer Console: F12
- Go to Console tab

### 3. Complete Flow
1. Fill in Patient Info
2. Answer Questionnaire (10 questions)
3. Upload an Image
4. View Results

### 4. Verify CNN Prediction
In Results page, look for:
```
┌─ Image Analysis ─────────┐
│                          │
│ CNN Model Confidence:    │
│ ████████░ 80%           │
│                          │
│ Prediction:              │
│ Elevated Risk           │
│                          │
│ Contribution:            │
│ 60%                     │
│                          │
│ Attention Regions:       │
│ [None available]         │
└──────────────────────────┘
```

## 🐛 Debug Console Output

When testing, you should see these console logs (F12 → Console):

```javascript
// When submitting questionnaire:
[Frontend] Questionnaire API Response: {...}
[Frontend] Parsed QuestionnaireResult: {...}

// When uploading image:
[Frontend] Image API Response: {...}
[Frontend] Parsed ImageResult: {...}

// When calculating combined:
[Frontend] Combined Result: {
  mlConfidence: 0.0004,
  cnnConfidence: 0.9982,
  combinedConfidence: 0.9302,
  mlContribution: 0.0002,
  cnnContribution: 0.5989,
  riskLevel: "HIGH"
}
[Frontend] Final Combined Result: {...}
```

## ⚙️ Key Changes Made

### API Response Mapping
```typescript
// Backend sends snake_case
{
  "attention_regions": [...],
  "heatmap_base64": "...",
  "llm_explanation": "..."
}

// Frontend converts to camelCase
{
  attentionRegions: [...],
  heatmapBase64: "...",
  llmExplanation: "..."
}
```

### Weight Distribution
- Questionnaire ML: 40%
- Image CNN: 60%
- Combined = (ML × 0.4) + (CNN × 0.6)

### Risk Levels
- HIGH: Combined > 0.75
- MODERATE: 0.50 < Combined ≤ 0.75
- LOW: Combined ≤ 0.50

## 📊 Expected Results

### Test with "Low Risk" Questionnaire
```
ML Confidence:  0.0004 (40% = 0.00016)
CNN Confidence: 0.9982 (60% = 0.59892)
─────────────────────────────────────
Combined:       0.59908 → MODERATE Risk
```

### Test with "High Risk" Questionnaire
```
ML Confidence:  0.9994 (40% = 0.39976)
CNN Confidence: 0.8841 (60% = 0.53046)
─────────────────────────────────────
Combined:       0.93022 → HIGH Risk
```

## ✅ Checklist

- [ ] Frontend is running at http://localhost:8081
- [ ] Backend is running at http://localhost:5000
- [ ] CNN model is loaded (check backend terminal for [OK])
- [ ] Questionnaire form displays all 10 questions
- [ ] Image upload form works
- [ ] Results page shows both cards (Questionnaire + Image Analysis)
- [ ] CNN Confidence appears in Image Analysis card
- [ ] Combined risk level reflects both predictions
- [ ] Console logs show proper API responses

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| CNN predictions not showing | Open F12 console, check logs for errors |
| Image Analysis card empty | Verify `/api/predict/image` returns 200 in Network tab |
| Wrong risk level | Check combined calculation in console logs |
| "Not available" message | CNN model might not be loaded; check backend terminal |
| React errors | Run `npm run build` to check for TypeScript errors |

## 📁 Files Modified

- `src/hooks/useScreening.ts` - Fixed API response parsing
- `src/types/asd.ts` - Made imageDetails nullable
- Backend: Already working, no changes needed

---

**Status:** ✅ Ready to use | **Last Updated:** Jan 20, 2026
