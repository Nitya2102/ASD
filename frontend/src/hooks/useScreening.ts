import { useState, useCallback } from 'react';
import { 
  ScreeningState, 
  PatientInfo, 
  QuestionnaireResponses, 
  QuestionnaireResult, 
  ImageResult, 
  CombinedResult 
} from '@/types/asd';

const API_BASE = 'http://localhost:5000';

const initialResponses: QuestionnaireResponses = {
  A1: null, A2: null, A3: null, A4: null, A5: null,
  A6: null, A7: null, A8: null, A9: null, A10: null,
};

const initialState: ScreeningState = {
  step: 'patient-info',
  patientInfo: null,
  responses: initialResponses,
  imageFile: null,
  imagePreview: null,
  questionnaireResult: null,
  imageResult: null,
  combinedResult: null,
  isLoading: false,
  error: null,
};

export function useScreening() {
  const [state, setState] = useState<ScreeningState>(initialState);

  const setPatientInfo = useCallback((info: PatientInfo) => {
    setState(prev => ({
      ...prev,
      patientInfo: info,
      step: 'questionnaire',
    }));
  }, []);

  const setResponse = useCallback(
    (questionId: keyof QuestionnaireResponses, value: 'yes' | 'no') => {
      setState(prev => ({
        ...prev,
        responses: {
          ...prev.responses,
          [questionId]: value,
        },
      }));
    },
    []
  );

  const setImage = useCallback((file: File | null, preview: string | null) => {
    setState(prev => ({
      ...prev,
      imageFile: file,
      imagePreview: preview,
    }));
  }, []);

  const goToStep = useCallback((step: ScreeningState['step']) => {
    setState(prev => ({ ...prev, step }));
  }, []);

  // ==========================================================
  // SUBMIT QUESTIONNAIRE (FIXED)
  // ==========================================================
  const submitQuestionnaire = useCallback(async () => {
    if (!state.patientInfo) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(`${API_BASE}/api/predict/questionnaire`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          age: state.patientInfo.age,
          sex: state.patientInfo.sex,
          jaundice: state.patientInfo.jaundice ? 'yes' : 'no',
          family_asd: state.patientInfo.familyAsd ? 'yes' : 'no',
          responses: state.responses,
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }

      const data = await response.json();

      console.log('[Frontend] Questionnaire API Response:', data);

      const result: QuestionnaireResult = {
        source: 'questionnaire',
        prediction: data.prediction,
        confidence: data.confidence,
        riskLevel: (data.risk_level || 'LOW') as any,
        totalScore: data.total_score || 0,
        concerns: [], // Backend doesn't provide, generate frontend version if needed
        recommendations: [], // Backend doesn't provide, generate frontend version if needed
      };

      console.log('[Frontend] Parsed QuestionnaireResult:', result);

      setState(prev => ({
        ...prev,
        questionnaireResult: result,
        step: 'image-analysis',
        isLoading: false,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'Failed to process questionnaire. Please try again.',
        isLoading: false,
      }));
    }
  }, [state.patientInfo, state.responses]);

  // ==========================================================
  // SUBMIT IMAGE (FIXED)
  // ==========================================================
  const submitImage = useCallback(async () => {
    if (!state.imageFile) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const formData = new FormData();
      formData.append('image', state.imageFile);

      const response = await fetch(`${API_BASE}/api/predict/image`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Image analysis failed: ${response.status}`);
      }

      const data = await response.json();

      console.log('[Frontend] Image API Response:', data);

      // Check for errors from backend
      if (data.error) {
        throw new Error(data.error);
      }

      const result: ImageResult = {
        source: 'image',
        prediction: data.prediction,
        confidence: data.confidence,
        heatmapBase64: data.heatmap_base64 || '',
        limeBase64: data.lime_base64 || '',
        attentionRegions: data.attention_regions || [],
        llmExplanation: data.llm_explanation || 'No explanation available',
        facialRegions: Array.isArray(data.facial_regions) ? data.facial_regions : (data.facial_regions || {}),
      };

      console.log('[Frontend] Parsed ImageResult:', result);

      const q = state.questionnaireResult!;
      const mlWeight = 0.4;
      const cnnWeight = 0.6;

      const combinedConfidence =
        q.confidence * mlWeight + result.confidence * cnnWeight;

      const combined: CombinedResult = {
        prediction: combinedConfidence > 0.5 ? 1 : 0,
        predictionLabel:
          combinedConfidence > 0.5 ? 'ELEVATED_RISK' : 'LOW_RISK',
        confidence: combinedConfidence,
        riskLevel:
          combinedConfidence > 0.75
            ? 'HIGH'
            : combinedConfidence > 0.5
            ? 'MODERATE'
            : 'LOW',
        mlContribution: q.confidence * mlWeight,
        cnnContribution: result.confidence * cnnWeight,
        questionnaireDetails: q,
        imageDetails: result,
      };

      console.log('[Frontend] Combined Result:', {
        mlConfidence: q.confidence,
        cnnConfidence: result.confidence,
        combinedConfidence,
        mlContribution: q.confidence * mlWeight,
        cnnContribution: result.confidence * cnnWeight,
        riskLevel: combined.riskLevel,
      });
      console.log('[Frontend] Final Combined Result:', combined);

      setState(prev => ({
        ...prev,
        imageResult: result,
        combinedResult: combined,
        step: 'results',
        isLoading: false,
      }));
    } catch (error) {
      console.error('[Frontend] Image submission error:', error);
      setState(prev => ({
        ...prev,
        error: `Failed to analyze image: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isLoading: false,
      }));
    }
  }, [state.imageFile, state.questionnaireResult]);

  // ==========================================================
  // SKIP IMAGE
  // ==========================================================
  const skipImageAnalysis = useCallback(() => {
    if (!state.questionnaireResult) return;

    const q = state.questionnaireResult;

    const combined: CombinedResult = {
      prediction: q.prediction,
      predictionLabel: q.prediction ? 'ELEVATED_RISK' : 'LOW_RISK',
      confidence: q.confidence,
      riskLevel: q.riskLevel,
      mlContribution: q.confidence,
      cnnContribution: 0,
      questionnaireDetails: q,
      imageDetails: null,
    };

    setState(prev => ({
      ...prev,
      combinedResult: combined,
      step: 'results',
    }));
  }, [state.questionnaireResult]);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return {
    state,
    setPatientInfo,
    setResponse,
    setImage,
    goToStep,
    submitQuestionnaire,
    submitImage,
    skipImageAnalysis,
    reset,
  };
}
