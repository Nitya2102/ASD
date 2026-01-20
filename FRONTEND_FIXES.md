# Frontend CNN Prediction Display Fixes

## Issue
The backend was successfully loading the CNN model and generating predictions, but the frontend was not properly displaying them.

## Root Causes Identified

1. **Snake_case to camelCase mapping mismatch**: The backend API response uses snake_case keys, but the frontend hook wasn't converting them properly.
   - `attention_regions` → should map to `attentionRegions`
   - `heatmap_base64` → should map to `heatmapBase64`
   - `llm_explanation` → should map to `llmExplanation`
   - `facial_regions` → should map to `facialRegions`

2. **Type definition issue**: The `CombinedResult.imageDetails` was typed as non-nullable `ImageResult`, but when skipping image analysis, the code tried to set it to `null`.

3. **Missing error handling**: The image prediction response wasn't checking for backend errors.

## Files Modified

### 1. `src/hooks/useScreening.ts`
**Changes:**
- Added console logging to track API responses for debugging
- Fixed ImageResult parsing to properly handle snake_case to camelCase conversion
- Added error checking for backend error responses
- Added detailed logging for combined prediction calculations
- Removed `null as any` type casting in skipImageAnalysis

**Key sections updated:**
```typescript
// Questionnaire response parsing
const result: QuestionnaireResult = {
  source: 'questionnaire',
  prediction: data.prediction,
  confidence: data.confidence,
  riskLevel: data.risk_level || 'LOW',  // proper mapping
  totalScore: data.total_score || 0,
  concerns: data.concerns ?? [],
  recommendations: data.recommendations ?? [],
};

// Image response parsing
const result: ImageResult = {
  source: 'image',
  prediction: data.prediction,
  confidence: data.confidence,
  heatmapBase64: data.heatmap_base64 || '',     // snake_case mapping
  limeBase64: data.lime_base64 || '',           // snake_case mapping
  attentionRegions: data.attention_regions || [],// snake_case mapping
  llmExplanation: data.llm_explanation || 'No explanation available',
  facialRegions: data.facial_regions || {},     // snake_case mapping
};
```

### 2. `src/types/asd.ts`
**Changes:**
- Made `CombinedResult.imageDetails` nullable (optional)
- Changed from `imageDetails: ImageResult` to `imageDetails: ImageResult | null`

This allows proper typing when image analysis is skipped.

### 3. Console Logging Added
Three logging points for debugging:
1. **Questionnaire Response**: Logs the raw API response from questionnaire endpoint
2. **Image Response**: Logs the raw API response from image prediction endpoint
3. **Combined Calculation**: Shows ML confidence, CNN confidence, combined confidence, and risk level

## Backend Response Format
The backend `/api/predict/image` returns:
```json
{
  "source": "image",
  "prediction": 1,
  "confidence": 0.998,
  "attention_regions": [],
  "heatmap_base64": "",
  "llm_explanation": "Explainable AI module not available",
  "facial_regions": {}
}
```

## Testing Recommendations

1. **Open Browser Console** (F12) to see debug logs
2. **Fill out questionnaire** - watch console for questionnaire response logs
3. **Upload an image** - watch console for image prediction response logs  
4. **View Results** - confirm CNN confidence is displayed (60% weight in combined score)
5. **Check Risk Level** - should reflect both questionnaire (40%) and image (60%) predictions

## Expected Result
✅ CNN predictions now properly display in the Results section
✅ Combined risk calculation shows weighted contributions from both models
✅ Console logs help debug any future issues
